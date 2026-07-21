import { useState, useEffect, useMemo, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { useDiscovery } from "../hooks/useDiscovery";
import { apiService } from "../services/api";
import { useMarketContext } from "../hooks/useMarketContext";
import { useIdempotentAction } from "../hooks/useIdempotentAction";
import { MarketContextPanel } from "../components/discovery/MarketContextPanel";
import { HorizonTabs } from "../components/discovery/HorizonTabs";
import { StockList } from "../components/discovery/StockList";
import { StockDetail } from "../components/analysis/StockDetail";
import { DispatchProgressModal } from "../components/dispatch/DispatchProgressModal";
import { SplitButton } from "../components/shared/SplitButton";
import { Spinner } from "../components/shared/Spinner";
import { ArrowLeft, AlertTriangle, X, Download } from "lucide-react";
import type { Horizon, AnalyzeResponse, DispatchSymbolStatus } from "../types";
import { generateDiscoveryPdf } from "../utils/generateDiscoveryPdf";

type RetryAction = "discover" | "details" | "dispatch" | "analysis";

interface OperationError {
  message: string;
  retryAction: RetryAction;
  horizon?: Horizon;
}

interface ActiveDispatch {
  runId: string;
  horizon: Horizon;
}

interface RequestError {
  response?: { status?: number; data?: { detail?: string } };
  message?: string;
  isDuplicate?: boolean;
}

function asRequestError(error: unknown): RequestError {
  return typeof error === "object" && error !== null ? (error as RequestError) : {};
}

function getErrorMessage(error: unknown, fallback: string) {
  const requestError = asRequestError(error);
  return requestError.response?.data?.detail || requestError.message || fallback;
}

function isDuplicateError(error: unknown) {
  return Boolean(asRequestError(error).isDuplicate);
}

function isHorizon(value: unknown): value is Horizon {
  return value === "SHORT" || value === "MID" || value === "LONG";
}

function readActiveDispatch(): ActiveDispatch | null {
  const savedDispatch = localStorage.getItem("active_dispatch");
  if (!savedDispatch) return null;

  try {
    const parsed: unknown = JSON.parse(savedDispatch);
    if (
      typeof parsed === "object" &&
      parsed !== null &&
      "runId" in parsed &&
      typeof parsed.runId === "string" &&
      "horizon" in parsed &&
      isHorizon(parsed.horizon)
    ) {
      return { runId: parsed.runId, horizon: parsed.horizon };
    }
  } catch {
    return null;
  }

  return null;
}

function isPreviousCalendarDay(timestamp?: string) {
  if (!timestamp) return false;
  const dataDate = new Date(timestamp);
  const today = new Date();
  return (
    dataDate.getDate() !== today.getDate() ||
    dataDate.getMonth() !== today.getMonth() ||
    dataDate.getFullYear() !== today.getFullYear()
  );
}

export function Discovery() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { symbol: routeSymbol } = useParams();
  const {
    data: discovery,
    isLoading,
    error: discoveryError,
    refetch: retryDiscoveryFetch,
  } = useDiscovery();
  const { data: marketContext } = useMarketContext();

  const [searchParams, setSearchParams] = useSearchParams();
  const selectedHorizon = (searchParams.get("horizon") as Horizon) || "SHORT";
  const setSelectedHorizon = (val: Horizon) => {
    setSearchParams({ horizon: val });
  };

  // Single-stock analysis triggers
  const [selectedStockAnalysis, setSelectedStockAnalysis] = useState<AnalyzeResponse | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [detailRetryToken, setDetailRetryToken] = useState(0);
  const [operationError, setOperationError] = useState<OperationError | null>(null);

  
  // Dispatch Progress state
  const [activeDispatch, setActiveDispatch] = useState<ActiveDispatch | null>(readActiveDispatch);

  // Update localStorage when activeDispatch changes
  useEffect(() => {
    if (activeDispatch) {
      localStorage.setItem("active_dispatch", JSON.stringify(activeDispatch));
    } else {
      localStorage.removeItem("active_dispatch");
    }
  }, [activeDispatch]);
  
  // Keep track of active statuses inside dispatch runs in-memory
  const [inMemoryDispatchStatus, setInMemoryDispatchStatus] = useState<Record<string, DispatchSymbolStatus>>(() => {
    const saved = sessionStorage.getItem("inMemoryDispatchStatus");
    return saved ? JSON.parse(saved) : {};
  });
  
  // Background polling state for when the modal is closed
  const [backgroundDispatchId, setBackgroundDispatchId] = useState<string | null>(() => {
    return sessionStorage.getItem("backgroundDispatchId") || null;
  });
  const [backgroundDispatchStats, setBackgroundDispatchStats] = useState<{done: number, total: number} | null>(() => {
    const saved = sessionStorage.getItem("backgroundDispatchStats");
    return saved ? JSON.parse(saved) : null;
  });
  const [backgroundDispatchHorizon, setBackgroundDispatchHorizon] = useState<Horizon | null>(() => {
    return (sessionStorage.getItem("backgroundDispatchHorizon") as Horizon) || null;
  });
  const [showCompletionPopup, setShowCompletionPopup] = useState(false);

  useEffect(() => {
    sessionStorage.setItem("inMemoryDispatchStatus", JSON.stringify(inMemoryDispatchStatus));
  }, [inMemoryDispatchStatus]);

  useEffect(() => {
    if (backgroundDispatchId) sessionStorage.setItem("backgroundDispatchId", backgroundDispatchId);
    else sessionStorage.removeItem("backgroundDispatchId");
  }, [backgroundDispatchId]);

  useEffect(() => {
    if (backgroundDispatchStats) sessionStorage.setItem("backgroundDispatchStats", JSON.stringify(backgroundDispatchStats));
    else sessionStorage.removeItem("backgroundDispatchStats");
  }, [backgroundDispatchStats]);

  useEffect(() => {
    if (backgroundDispatchHorizon) sessionStorage.setItem("backgroundDispatchHorizon", backgroundDispatchHorizon);
    else sessionStorage.removeItem("backgroundDispatchHorizon");
  }, [backgroundDispatchHorizon]);

  useEffect(() => {
    if (!backgroundDispatchId) return;
    const interval = setInterval(async () => {
      try {
        const res = await apiService.getDispatchStatus(backgroundDispatchId);
        if (res && res.stocks) {
          setInMemoryDispatchStatus((prev) => ({ ...prev, ...res.stocks }));
        }
        if (res) {
          setBackgroundDispatchStats({ done: res.done + res.errors, total: res.total });
        }
        if (res?.complete) {
          setBackgroundDispatchId(null);
          setBackgroundDispatchStats(null);
          setBackgroundDispatchHorizon(null);
          setShowCompletionPopup(true);
        }
      } catch (err) {
        console.warn("Background poll failed", err);
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [backgroundDispatchId]);

  // Check if data is from a previous calendar day
  const isDataOld = isPreviousCalendarDay(discovery?.timestamp);



  const selectedSymbol = routeSymbol?.toUpperCase() || null;

  // Filter stocks by selected horizon timeframe
  const activeStocks = useMemo(() => {
    return discovery?.buckets?.[selectedHorizon as keyof typeof discovery.buckets] || [];
  }, [selectedHorizon, discovery]);

  // Find the clicked stock across all buckets to identify its specific horizon if selectedHorizon is "ALL"
  const clickedStock = useMemo(() => {
    if (!selectedSymbol || !discovery) return null;
    return (
      discovery.buckets?.SHORT?.find(s => s.symbol === selectedSymbol) ||
      discovery.buckets?.MID?.find(s => s.symbol === selectedSymbol) ||
      discovery.buckets?.LONG?.find(s => s.symbol === selectedSymbol) ||
      null
    );
  }, [selectedSymbol, discovery]);

  // Removed useEffect that resets selected symbol when timeframe switches to allow persistence

  // Listen to custom event for in-app search triggers (from header)
  useEffect(() => {
    const handleSearch = (e: Event) => {
      const customEvent = e as CustomEvent<{ symbol: string }>;
      if (customEvent.detail?.symbol) {
        navigate(`/discovery/${customEvent.detail.symbol.toUpperCase()}?${searchParams.toString()}`);
      }
    };

    window.addEventListener("stockSearchSelect", handleSearch);
    return () => window.removeEventListener("stockSearchSelect", handleSearch);
  }, [navigate, searchParams]);

  // Fetch full stock analysis when a stock row is clicked
  useEffect(() => {
    async function loadAnalysis() {
      if (!selectedSymbol) {
        setSelectedStockAnalysis(null);
        return;
      }

      setIsDetailLoading(true);
      setOperationError(null);
      try {
        const embeddedRecId = clickedStock?.recommendation_id;
        const embeddedResponse = clickedStock?.full_response;

        if (embeddedResponse) {
          setSelectedStockAnalysis(embeddedResponse);
          setIsDetailLoading(false);
          return;
        }

        const cache = inMemoryDispatchStatus[selectedSymbol];
        if (cache?.status === "done" && cache?.full_response) {
          setSelectedStockAnalysis(cache.full_response);
          setIsDetailLoading(false);
          return;
        }

        // Prefer fetching the exact analysis row BY ID (recommendation_id) from
        // the DB, not by symbol.
        const cachedRecId = cache?.recommendation_id || embeddedRecId;
        if (cachedRecId) {
          const byId = await apiService.getHistoryDetail(cachedRecId);
          setSelectedStockAnalysis(byId);
          setIsDetailLoading(false);
          return;
        }

        // No id known yet (e.g. freshly discovered, never analysed): fall back to
        // the by-symbol latest. Its response carries recommendation_id, so any
        // subsequent open resolves by id.
        const targetHorizon = selectedHorizon;
        const latestResponse = await apiService.getLatestAnalysis(selectedSymbol, targetHorizon);
        setSelectedStockAnalysis(latestResponse);
      } catch (error: unknown) {
        if (asRequestError(error).response?.status === 404) {
          setSelectedStockAnalysis({
            run_id: "",
            symbol: selectedSymbol,
            recommendation: "WAIT",
            confidence: 0,
            narrative: "",
            key_risks: [],
            key_catalysts: [],
            agent_signals: { technical: "HOLD", fundamental: "HOLD", sentiment: "HOLD", chart_pattern: "HOLD" },
            validator_issues: [],
            validator_status: "accepted",
            macro_regime: "SIDEWAYS",
            market_pulse_score: 50,
            errors: [],
            timestamp: new Date().toISOString(),
            recommendation_id: null,
          });
        } else {
          setOperationError({
            message: getErrorMessage(error, "Could not load this stock's evidence."),
            retryAction: "details",
          });
        }
      } finally {
        setIsDetailLoading(false);
      }
    }

    loadAnalysis();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSymbol, selectedHorizon, clickedStock, detailRetryToken]);

  // Trigger discovery scans
  const _runDiscovery = useCallback(async (horizonParam: string) => {
    setOperationError(null);
    try {
      await apiService.runDiscovery(horizonParam);
      await queryClient.invalidateQueries({ queryKey: ["discovery"] });
      await queryClient.invalidateQueries({ queryKey: ["marketContext"] });
    } catch (err: unknown) {
      if (!isDuplicateError(err)) {
        setOperationError({
          message: getErrorMessage(err, "Discovery could not reach the research service."),
          retryAction: "discover",
        });
      }
    }
  }, [queryClient]);
  const [handleRunDiscovery, _isDiscovering] = useIdempotentAction(_runDiscovery);

  const [isResumingDiscovery, setIsResumingDiscovery] = useState(
    () => Boolean(localStorage.getItem("active_discovery_job")),
  );

  useEffect(() => {
    const activeJobId = localStorage.getItem("active_discovery_job");
    const activeHorizon = localStorage.getItem("active_discovery_horizon") || "ALL";
    if (activeJobId) {
      apiService.pollDiscoveryJob(activeJobId, activeHorizon)
        .then(() => {
          localStorage.removeItem("active_discovery_job");
          localStorage.removeItem("active_discovery_horizon");
          queryClient.invalidateQueries({ queryKey: ["discovery"] });
          queryClient.invalidateQueries({ queryKey: ["marketContext"] });
        })
        .catch((err) => {
          setOperationError({
            message: getErrorMessage(err, "The previous discovery run could not be resumed."),
            retryAction: "discover",
          });
          localStorage.removeItem("active_discovery_job");
          localStorage.removeItem("active_discovery_horizon");
        })
        .finally(() => setIsResumingDiscovery(false));
    }
  }, [queryClient]);

  const isDiscovering = _isDiscovering || isResumingDiscovery;

  // Dispatch Confirm Modal State
  const [dispatchConfirmModal, setDispatchConfirmModal] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
  }>({ isOpen: false, title: "", message: "", onConfirm: () => {} });

  // Trigger dispatch analyses
  const _analyseAll = useCallback(async (horizonParam: Horizon) => {
    if (!discovery?.run_id) return;
    if (activeDispatch) return;
    
    if (horizonParam === "MID" || horizonParam === "LONG") {
      setDispatchConfirmModal({
        isOpen: true,
        title: "Confirm Analysis Run",
        message: "Are you sure you want to run that? We already have run the thing for MID and LONG.",
        onConfirm: async () => {
          setDispatchConfirmModal(prev => ({ ...prev, isOpen: false }));
          try {
            const response = await apiService.dispatchAnalyseAll(discovery.run_id, horizonParam);
            setActiveDispatch({ runId: response.run_id, horizon: horizonParam });
          } catch (err: unknown) {
            if (!isDuplicateError(err)) {
              setOperationError({
                message: getErrorMessage(err, "Could not start the evidence analysis."),
                retryAction: "dispatch",
                horizon: horizonParam,
              });
            }
          }
        }
      });
      return;
    } else if (horizonParam === "SHORT") {
      const shortRunCount = parseInt(localStorage.getItem("short_run_count") || "0", 10);
      if (shortRunCount >= 3) {
        setDispatchConfirmModal({
          isOpen: true,
          title: "Confirm Analysis Run",
          message: "Are you sure you want to run that? SHORT horizon has already been run 3 times.",
          onConfirm: async () => {
            setDispatchConfirmModal(prev => ({ ...prev, isOpen: false }));
            localStorage.setItem("short_run_count", (shortRunCount + 1).toString());
            try {
              const response = await apiService.dispatchAnalyseAll(discovery.run_id, horizonParam);
              setActiveDispatch({ runId: response.run_id, horizon: horizonParam });
            } catch (err: unknown) {
              if (!isDuplicateError(err)) {
                setOperationError({
                  message: getErrorMessage(err, "Could not start the evidence analysis."),
                  retryAction: "dispatch",
                  horizon: horizonParam,
                });
              }
            }
          }
        });
        return;
      }
      localStorage.setItem("short_run_count", (shortRunCount + 1).toString());
    }

    try {
      const response = await apiService.dispatchAnalyseAll(discovery.run_id, horizonParam);
      setActiveDispatch({ runId: response.run_id, horizon: horizonParam });
    } catch (err: unknown) {
      if (!isDuplicateError(err)) {
        setOperationError({
          message: getErrorMessage(err, "Could not start the evidence analysis."),
          retryAction: "dispatch",
          horizon: horizonParam,
        });
      }
    }
  }, [discovery, activeDispatch]);
  const [handleAnalyseAll] = useIdempotentAction(_analyseAll);

  // Perform single ad-hoc analysis
  const _singleStockAnalysis = useCallback(async () => {
    if (!selectedSymbol) return;
    setOperationError(null);
    try {
      const targetHorizon = selectedHorizon;
      const response = await apiService.analyzeStock(selectedSymbol, targetHorizon);
      setSelectedStockAnalysis(response);
      setInMemoryDispatchStatus((prev) => ({
        ...prev,
        [selectedSymbol]: {
          status: "done",
          recommendation: response.recommendation,
          confidence: response.confidence,
          full_response: response,
        },
      }));
    } catch (err: unknown) {
      if (!isDuplicateError(err)) {
        setOperationError({
          message: getErrorMessage(err, "Could not analyze this stock's evidence."),
          retryAction: "analysis",
        });
      }
    }
  }, [selectedSymbol, selectedHorizon]);
  const [handleSingleStockAnalysis, isSingleAnalysing] = useIdempotentAction(_singleStockAnalysis);

  // Callback to sync items in-memory when progress completes
  const handleCloseDispatch = () => {
    if (activeDispatch?.runId) {
      apiService.getDispatchStatus(activeDispatch.runId).then((res) => {
        setInMemoryDispatchStatus((prev) => ({
          ...prev,
          ...res.stocks,
        }));
        if (res.complete) {
          queryClient.invalidateQueries({ queryKey: ["discovery"] });
        } else {
          setBackgroundDispatchId(activeDispatch.runId);
          setBackgroundDispatchStats({ done: res.done + res.errors, total: res.total });
          setBackgroundDispatchHorizon(activeDispatch.horizon);
        }
      }).catch((err: unknown) => console.warn(err));
    }
    setActiveDispatch(null);
  };

  const handleOpenBackgroundDispatch = () => {
    if (backgroundDispatchId) {
      setActiveDispatch({
        runId: backgroundDispatchId,
        horizon: backgroundDispatchHorizon || selectedHorizon
      });
      setBackgroundDispatchId(null);
      setBackgroundDispatchStats(null);
      setBackgroundDispatchHorizon(null);
    }
  };

  const handleCloseCompletionPopup = () => {
    setShowCompletionPopup(false);
    queryClient.invalidateQueries({ queryKey: ["discovery"] });
  };

  const getDiscoveryCounts = () => {
    return {
      SHORT: discovery?.buckets?.SHORT?.length || 0,
      MID: discovery?.buckets?.MID?.length || 0,
      LONG: discovery?.buckets?.LONG?.length || 0,
    };
  };

  const retryFailedOperation = () => {
    if (!operationError) {
      void retryDiscoveryFetch();
      return;
    }

    const failed = operationError;
    setOperationError(null);
    if (failed.retryAction === "details") {
      setDetailRetryToken((token) => token + 1);
    } else if (failed.retryAction === "analysis") {
      void handleSingleStockAnalysis();
    } else if (failed.retryAction === "dispatch") {
      void handleAnalyseAll(failed.horizon || selectedHorizon);
    } else {
      void handleRunDiscovery("ALL");
    }
  };



  return (
    <div className="space-y-5 animate-in fade-in duration-200">
      
      {/* 1. MARKET PREAMBLE INTELLIGENCE ROW */}
      <MarketContextPanel />

      {(operationError || discoveryError) && (
        <div
          role="alert"
          className="flex flex-col gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-red-800 sm:flex-row sm:items-center sm:justify-between"
        >
          <div className="flex items-start gap-2">
            <AlertTriangle size={18} className="mt-0.5 shrink-0" aria-hidden="true" />
            <div>
              <p className="text-sm font-bold">Research data could not be loaded</p>
              <p className="mt-0.5 text-xs">
                {operationError?.message || getErrorMessage(discoveryError, "The research service is unavailable.")}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={retryFailedOperation}
            className="shrink-0 rounded-lg border border-red-200 bg-white px-4 py-2 text-xs font-bold text-red-700 hover:bg-red-100"
          >
            Retry
          </button>
        </div>
      )}

      {/* 2. MARKET SCANNER CONSOLE HEADER */}
      <div className="flex flex-col sm:flex-row justify-between items-center bg-white border border-border rounded-xl p-4 shadow-sm w-full gap-4 sm:gap-0 relative">
        
        {/* Fixed Center Background Dispatch Indicator */}
        {backgroundDispatchId && (
          <button
            onClick={handleOpenBackgroundDispatch}
            title="Click to view full progress modal"
            className="fixed top-4 left-1/2 -translate-x-1/2 z-[150] bg-navy hover:bg-navy-light text-white px-4 py-2 rounded-full text-xs font-bold shadow-2xl flex items-center gap-2 border border-white/20 animate-in slide-in-from-top-4 duration-300 transition-all hover:scale-105 active:scale-95"
          >
            <Spinner size="sm" className="text-white" />
            <span>
              Analysis Running... 
              {backgroundDispatchStats && ` (${backgroundDispatchStats.done}/${backgroundDispatchStats.total})`}
            </span>
            <span className="text-[10px] bg-white/25 text-white/90 px-1.5 py-0.5 rounded font-medium">View</span>
          </button>
        )}

        {/* LEFT: Keep the judged flow focused on one selected stock. */}
        <div className="w-full sm:w-auto sm:ml-4">
          <p className="text-xs font-semibold text-muted">
            Select one candidate below to inspect and analyze its evidence.
          </p>
        </div>

        {/* RIGHT: Run Scans & Download */}
        <div className="w-full sm:w-auto flex justify-center sm:justify-end gap-2">
          {activeStocks.length > 0 && discovery && (
            <SplitButton
              variant="secondary"
              mainLabel="Download Scan"
              icon={<Download size={16} className="text-muted" />}
              onMainClick={() => {
                const allStocks = [
                  ...(discovery.buckets?.SHORT || []),
                  ...(discovery.buckets?.MID || []),
                  ...(discovery.buckets?.LONG || []),
                ];
                generateDiscoveryPdf(allStocks, "ALL", discovery.timestamp, marketContext);
              }}
              dropdownItems={[
                { label: "Download ALL", onClick: () => {
                    const allStocks = [
                      ...(discovery.buckets?.SHORT || []),
                      ...(discovery.buckets?.MID || []),
                      ...(discovery.buckets?.LONG || []),
                    ];
                    generateDiscoveryPdf(allStocks, "ALL", discovery.timestamp, marketContext);
                }},
                { label: "Download SHORT", onClick: () => generateDiscoveryPdf(discovery.buckets?.SHORT || [], "SHORT", discovery.timestamp, marketContext) },
                { label: "Download MID", onClick: () => generateDiscoveryPdf(discovery.buckets?.MID || [], "MID", discovery.timestamp, marketContext) },
                { label: "Download LONG", onClick: () => generateDiscoveryPdf(discovery.buckets?.LONG || [], "LONG", discovery.timestamp, marketContext) },
              ]}
            />
          )}
          <button
            type="button"
            disabled={isDiscovering}
            onClick={() => handleRunDiscovery("ALL")}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-accent hover:bg-accent-dark text-white rounded-lg text-xs md:text-sm font-bold shadow-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isDiscovering ? (
              <>
                <Spinner size="sm" className="border-t-transparent border-white" />
                <span>Running...</span>
              </>
            ) : (
              <span>🔎 Discover Stocks</span>
            )}
          </button>
        </div>
      </div>

      {isDataOld && !isDiscovering && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-center gap-3 text-amber-800 animate-in slide-in-from-top-2">
          <AlertTriangle size={18} className="text-amber-600 flex-shrink-0" />
          <p className="text-sm font-medium">
            You are viewing old data from {new Date(discovery!.timestamp).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}. Please run <b>Discover Stocks</b> to refresh for new data.
          </p>
        </div>
      )}

      {/* TIMEFRAME HORIZON TABS */}
      <div className="bg-white border border-border rounded-xl p-3 md:p-3.5 shadow-sm space-y-4">
        <HorizonTabs
          selected={selectedHorizon}
          onChange={setSelectedHorizon}
          counts={getDiscoveryCounts()}
        />

        {isLoading || isDiscovering ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-3">
            <Spinner size="lg" />
            <p className="text-xs text-muted font-medium">{isDiscovering ? "Running live market scans and assembling data..." : "Consulting pre-amble planners and scanners..."}</p>
          </div>
        ) : (
          <div className="w-full">
            {!selectedSymbol ? (
              <StockList
                stocks={activeStocks}
                selectedSymbol={selectedSymbol}
                onSelect={(sym) => navigate(`/discovery/${sym}?${searchParams.toString()}`)}
                dispatchState={inMemoryDispatchStatus}
              />
            ) : (
              <div className="animate-in slide-in-from-right-4 duration-300">
                <button
                  type="button"
                  onClick={() => navigate(`/discovery?${searchParams.toString()}`)}
                  className="inline-flex items-center gap-1.5 mb-4 px-4 py-2 bg-white border border-border rounded-lg text-sm font-bold text-primary shadow-sm hover:bg-neutral-50 transition-colors"
                >
                  <ArrowLeft size={16} />
                  <span>Back to scan list</span>
                </button>
                <StockDetail
                  data={selectedStockAnalysis}
                  isLoading={isDetailLoading}
                  isAnalysing={isSingleAnalysing}
                  onAnalyseClick={handleSingleStockAnalysis}
                  symbolName={selectedSymbol}
                />
              </div>
            )}
          </div>
        )}
      </div>

      {/* DISPATCH PROGRESS QUEUE OVERLAY */}
      {activeDispatch && (
        <DispatchProgressModal
          runId={activeDispatch.runId}
          horizon={activeDispatch.horizon}
          onClose={handleCloseDispatch}
        />
      )}

      {/* CONFIRMATION MODAL */}
      {dispatchConfirmModal.isOpen && (
        <div className="fixed inset-0 z-[200] bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md border border-border animate-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center border-b border-border p-5">
              <div className="flex items-center gap-3 text-red-600">
                <div className="p-2 bg-red-50 rounded-full">
                  <AlertTriangle size={20} />
                </div>
                <h3 className="font-black text-lg text-primary tracking-tight">
                  {dispatchConfirmModal.title}
                </h3>
              </div>
              <button
                onClick={() => setDispatchConfirmModal(prev => ({ ...prev, isOpen: false }))}
                className="text-muted hover:text-primary transition-colors p-1 bg-neutral-50 hover:bg-neutral-100 rounded-lg border border-transparent hover:border-border"
              >
                <X size={18} />
              </button>
            </div>
            
            <div className="p-6">
              <p className="text-sm font-medium text-muted leading-relaxed">
                {dispatchConfirmModal.message}
              </p>
              
              <div className="flex gap-3 mt-8 w-full">
                <button
                  onClick={() => setDispatchConfirmModal(prev => ({ ...prev, isOpen: false }))}
                  className="flex-1 py-2.5 px-4 bg-white border border-border rounded-xl text-sm font-bold text-primary hover:bg-neutral-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={dispatchConfirmModal.onConfirm}
                  className="flex-1 py-2.5 px-4 bg-red-600 hover:bg-red-700 text-white rounded-xl text-sm font-bold shadow-md shadow-red-600/20 transition-all border border-red-600 hover:border-red-700"
                >
                  Yes, Run Anyway
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* COMPLETION POPUP */}
      {showCompletionPopup && (
        <div className="fixed inset-0 z-[200] bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md border border-border animate-in zoom-in-95 duration-200">
            <div className="p-6 text-center space-y-4">
              <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
              </div>
              <h3 className="font-black text-2xl text-primary tracking-tight">
                Analysis Complete
              </h3>
              <p className="text-sm font-medium text-muted leading-relaxed">
                The background analysis run has successfully finished processing. You can now view the updated stock recommendations.
              </p>
              <div className="mt-8">
                <button
                  onClick={handleCloseCompletionPopup}
                  className="w-full py-3 px-4 bg-accent hover:bg-accent-dark text-white rounded-xl text-sm font-bold shadow-md shadow-accent/20 transition-all"
                >
                  View Results
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

import type { AnalyzeResponse, DiscoveredStock, Signal } from "../../types";
import { AlertTriangle, CheckCircle2, CircleDot, PlayCircle, BarChart2, ExternalLink } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toVerdict } from "../../utils/verdict";

interface StockRowProps {
  stock: DiscoveredStock;
  isSelected: boolean;
  onClick: () => void;
  analysisState?: {
    recommendation?: Signal | null;
    recommendation_id?: string | null;
    confidence?: number | null;
    status?: "queued" | "running" | "done" | "error";
    run_id?: string;
    full_response?: AnalyzeResponse | null;
  } | null;
}

export function StockRow({ stock, isSelected, onClick, analysisState }: StockRowProps) {
  const navigate = useNavigate();
  // The detail panel renders full_response.recommendation, so the row badge must
  // read the SAME source first — otherwise the list and the detail can show
  // different verdicts for the same stock. Fall back to the flat fields only when
  // no snapshot is present. Everything is normalized to BUY/SELL/WAIT.
  const _fr = analysisState?.full_response || stock.full_response;
  const signal: Signal = toVerdict(
    _fr?.recommendation ??
    analysisState?.recommendation ??
    stock.recommendation
  );
  const isAnalysed =
    analysisState?.status === "done" ||
    !!analysisState?.full_response ||
    !!stock.recommendation_id;
  const isAnalysing = analysisState?.status === "running";

  const barColors: Record<Signal, string> = {
    BUY: "border-l-[6px] border-l-signal-buy border-y border-r",
    SELL: "border-l-[6px] border-l-signal-sell border-y border-r",
    WAIT: "border-l-[6px] border-l-signal-wait border-y border-r",
    HOLD: "border-l-[6px] border-l-signal-hold border-y border-r",
  };

  const bgStyle = isSelected
    ? "bg-accent-soft border-accent/40 shadow-sm"
    : "bg-white hover:bg-neutral-50/80 border-neutral-200";

  // CLEAN SEPARATION: Only show real F2 analysis data, never blend with discovery estimates
  const fullResponse = _fr;
  const hasAnalysis = isAnalysed && !!fullResponse;
  
  const entry = hasAnalysis ? fullResponse.entry_price : null;
  const target = hasAnalysis ? fullResponse.target_price : null;
  const stop = hasAnalysis ? fullResponse.stop_loss : null;
  const confidence = hasAnalysis ? fullResponse.confidence : null;
  const returnPct = hasAnalysis
    ? (fullResponse.upside_pct ?? fullResponse.profit_pct)
    : null;
  const evidence = stock.evidence || [];
  const newestEvidence = evidence.find((item) => item.status === "available") || evidence[0];
  const supportingCount = evidence.filter((item) => item.stance === "supporting").length;
  const contradictingCount = evidence.filter((item) => item.stance === "contradicting").length;
  const degradedCount = evidence.filter(
    (item) => item.status !== "available" || item.freshness === "stale"
  ).length;
  const dataQualityLabel = stock.data_quality
    ? stock.data_quality.charAt(0).toUpperCase() + stock.data_quality.slice(1)
    : "Not reported";

  return (
    <div
      onClick={onClick}
      className={`rounded-lg overflow-hidden cursor-pointer transition-all duration-150 flex flex-col md:flex-row items-stretch md:items-center p-4 gap-4 ${barColors[signal] || barColors.WAIT} ${bgStyle}`}
    >
      {/* 1. LEFT: Symbol, Score, Price */}
      <div className="flex justify-between items-center md:block md:w-[220px] shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h4 className="text-base font-black text-primary tracking-tight">{stock.symbol}</h4>
            {isAnalysed && (
              <span
                className={`inline-flex items-center gap-0.5 text-[9px] px-1 rounded-full font-semibold border ${
                  signal === "BUY"
                    ? "bg-signal-buy/10 text-signal-buy border-signal-buy/20"
                    : signal === "SELL"
                    ? "bg-signal-sell/10 text-signal-sell border-signal-sell/20"
                    : signal === "WAIT"
                    ? "bg-signal-wait/10 text-signal-wait border-signal-wait/20"
                    : "bg-signal-hold/10 text-signal-hold border-signal-hold/20"
                }`}
              >
                <CheckCircle2 size={10} />
                <span>ANALYSED</span>
              </span>
            )}
          </div>
          <div className="text-[11px] text-muted font-medium mt-0.5 flex items-center gap-1.5 flex-wrap">
            <span className="bg-neutral-100 text-muted px-1.5 py-0.5 rounded font-mono font-medium">
              Rank #{stock.rank || "—"}
            </span>
            <span>{stock.sector || "Investment"}</span>
          </div>
        </div>

        <div className="md:mt-3 flex items-center gap-4">
          <div>
            <div className="text-[10px] text-muted uppercase tracking-wider font-bold mb-0.5">Price</div>
            <div className="font-mono text-sm font-bold text-primary">
              {stock.close ? `₹${stock.close.toLocaleString("en-IN")}` : "—"}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-muted uppercase tracking-wider font-bold mb-0.5">Score</div>
            <div className="font-mono text-sm font-bold text-accent-dark">
              {stock.discovery_score || 0}
            </div>
          </div>
        </div>
      </div>

      {/* 2. MIDDLE: Metrics & Reasoning */}
      <div className="flex-1 md:px-6 md:border-l md:border-r border-neutral-100 py-2 space-y-3">
        {hasAnalysis ? (
          /* ── ANALYSIS METRICS — real F2 data ── */
          <div className="flex flex-wrap items-center gap-3 md:gap-5 bg-emerald-50/60 p-2.5 rounded border border-emerald-200/60">
            <div className="flex flex-col">
              <span className="text-[9px] text-muted font-bold uppercase tracking-wider">Entry</span>
              <span className="text-xs font-mono font-bold text-primary">{entry ? `₹${entry}` : "—"}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[9px] text-emerald-700 font-bold uppercase tracking-wider">Target</span>
              <span className="text-xs font-mono font-bold text-signal-buy">{target ? `₹${target}` : "—"}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[9px] text-red-700 font-bold uppercase tracking-wider">Stop Loss</span>
              <span className="text-xs font-mono font-bold text-signal-sell">{stop ? `₹${stop}` : "—"}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[9px] text-muted font-bold uppercase tracking-wider">Return</span>
              <span className="text-xs font-mono font-bold text-accent-dark">{returnPct ? `${returnPct > 0 ? "+" : ""}${returnPct.toFixed(1)}%` : "—"}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[9px] text-muted font-bold uppercase tracking-wider">Confidence</span>
              <span className="text-xs font-mono font-bold text-primary">{confidence ? `${confidence}%` : "—"}</span>
            </div>
          </div>
        ) : (
          /* ── SCREENING CRITERIA — raw TradingView data, not LLM estimates ── */
          <div className="flex flex-wrap items-center gap-3 md:gap-5 bg-neutral-50/50 p-2.5 rounded border border-neutral-100">
            {stock.rsi != null && (
              <div className="flex flex-col">
                <span className="text-[9px] text-muted font-bold uppercase tracking-wider">RSI</span>
                <span className="text-xs font-mono font-bold text-primary">{stock.rsi.toFixed(1)}</span>
              </div>
            )}
            {stock.pe_ratio != null && (
              <div className="flex flex-col">
                <span className="text-[9px] text-muted font-bold uppercase tracking-wider">P/E</span>
                <span className="text-xs font-mono font-bold text-primary">{stock.pe_ratio.toFixed(1)}</span>
              </div>
            )}
            {stock.roe != null && (
              <div className="flex flex-col">
                <span className="text-[9px] text-muted font-bold uppercase tracking-wider">ROE</span>
                <span className="text-xs font-mono font-bold text-primary">{stock.roe.toFixed(1)}%</span>
              </div>
            )}
            {stock.market_cap != null && (
              <div className="flex flex-col">
                <span className="text-[9px] text-muted font-bold uppercase tracking-wider">Mkt Cap</span>
                <span className="text-xs font-mono font-bold text-primary">₹{(stock.market_cap / 1e7).toFixed(0)} Cr</span>
              </div>
            )}
            {stock.relative_volume != null && (
              <div className="flex flex-col">
                <span className="text-[9px] text-muted font-bold uppercase tracking-wider">Rel. Vol</span>
                <span className="text-xs font-mono font-bold text-primary">{stock.relative_volume.toFixed(1)}x</span>
              </div>
            )}
            <span className="text-[10px] text-muted italic ml-auto flex items-center gap-1">
              <BarChart2 size={10} />
              Analyse for price targets
            </span>
          </div>
        )}
        
        {/* Evidence-first discovery context */}
        <div>
          <div className="text-[10px] font-bold text-muted uppercase flex items-center gap-1.5 mb-1.5">
            <BarChart2 size={12} />
            Why this surfaced now
          </div>
          <p className="text-xs text-primary leading-relaxed line-clamp-2">
            {stock.why_now || stock.catalyst || "The legacy result did not report a why-now explanation."}
          </p>
          {(stock.ai_reasoning || stock.catalyst) && (
            <p className="mt-1 text-[11px] text-muted leading-relaxed line-clamp-2">
              Initial thesis: {stock.ai_reasoning || stock.catalyst}
            </p>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-1.5 text-[9px] font-bold uppercase text-muted">
          <span className="rounded border border-border bg-neutral-50 px-1.5 py-0.5">
            Data: {dataQualityLabel}
          </span>
          <span className="rounded border border-border bg-neutral-50 px-1.5 py-0.5">
            {supportingCount} supporting
          </span>
          <span className="rounded border border-border bg-neutral-50 px-1.5 py-0.5">
            {contradictingCount} contradicting
          </span>
          <span className="rounded border border-border bg-neutral-50 px-1.5 py-0.5">
            {degradedCount} stale/unavailable
          </span>
          {newestEvidence && (
            newestEvidence.url ? (
              <a
                href={newestEvidence.url}
                target="_blank"
                rel="noreferrer"
                onClick={(event) => event.stopPropagation()}
                className="inline-flex items-center gap-1 rounded border border-accent/30 bg-accent/5 px-1.5 py-0.5 text-accent-dark hover:underline"
              >
                {newestEvidence.source}
                <ExternalLink size={9} aria-hidden="true" />
              </a>
            ) : (
              <span className="rounded border border-border bg-neutral-50 px-1.5 py-0.5 normal-case">
                Source: {newestEvidence.source}
              </span>
            )
          )}
          {newestEvidence?.as_of && (
            <span className="normal-case font-mono">
              as of {new Date(newestEvidence.as_of).toLocaleString()}
            </span>
          )}
        </div>
      </div>

      {/* 3. RIGHT: Status, Risks & Action */}
      <div className="flex flex-col md:w-[180px] shrink-0 justify-between items-end gap-3 pt-3 md:pt-0 border-t md:border-t-0 border-neutral-100">
        <div className="flex items-center justify-between w-full md:justify-end md:gap-3 text-xs">
          {/* Risks */}
          {stock.risk_flags && stock.risk_flags.length > 0 ? (
            <span className="text-signal-sell font-bold flex items-center gap-0.5 bg-signal-sell/5 px-1.5 py-0.5 rounded border border-signal-sell/10">
              <AlertTriangle size={12} />
              <span>{stock.risk_flags.length} risks</span>
            </span>
          ) : (
            <span className="text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-100 font-semibold">
              Low Risk
            </span>
          )}

          {/* Status Indicator */}
          <div className="flex items-center gap-1.5">
            {analysisState?.status === "running" && (
              <span className="text-blue-600 font-semibold animate-pulse flex items-center gap-1 text-[10px]">
                <CircleDot size={10} className="animate-spin" />
                <span>Analysing...</span>
              </span>
            )}
            {analysisState?.status === "queued" && (
              <span className="text-muted flex items-center gap-1 text-[10px]">
                <CircleDot size={10} />
                <span>Queued</span>
              </span>
            )}
            {analysisState?.status === "error" && (
              <span className="text-signal-sell font-semibold flex items-center gap-1 text-[10px]">
                <AlertTriangle size={10} />
                <span>Failed</span>
              </span>
            )}
            {!analysisState?.status && !isAnalysed && (
              <span className="text-muted flex items-center gap-0.5 text-[10px]">
                <PlayCircle size={11} />
                <span>Pending</span>
              </span>
            )}
          </div>
        </div>

        {/* Action Button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (isAnalysed) {
              const recId = analysisState?.recommendation_id || stock.recommendation_id;
              if (recId) {
                navigate(`/analyze/${recId}`);
              } else {
                onClick();
              }
            } else {
              onClick();
            }
          }}
          disabled={isAnalysing}
          className={`w-full px-4 py-2.5 text-xs font-black uppercase tracking-wider rounded-lg transition-all border ${
            isAnalysing
              ? "bg-neutral-50 text-muted border-border cursor-wait"
              : isAnalysed
              ? "bg-white text-primary border-border shadow-sm hover:border-accent hover:text-accent"
              : "bg-accent hover:bg-accent-dark text-white border-accent shadow-md shadow-accent/20"
          }`}
        >
          {isAnalysing ? "Analyzing..." : isAnalysed ? "View evidence" : "Analyze evidence"}
        </button>
        
        {/* Unique Run ID */}
        {analysisState?.run_id && (
          <div className="text-[9px] text-muted font-mono w-full text-right mt-[-4px]">
            ID: {analysisState.run_id.split("-").pop()}
          </div>
        )}
      </div>
    </div>
  );
}

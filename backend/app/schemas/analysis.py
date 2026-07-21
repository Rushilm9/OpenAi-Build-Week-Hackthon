"""
Analysis Schemas — Pydantic models for /discover and /analyze endpoints.
Updated for F1/F2 final: horizon-tagged buckets, chart pattern, validator, debate fields.
"""

from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional, List, Dict
from datetime import datetime, timezone


SourceStatus = Literal["available", "unavailable", "error"]
Freshness = Literal["live", "recent", "stale", "unknown"]
EvidenceStance = Literal["supporting", "contradicting", "neutral"]
ResearchPosture = Literal[
    "SUPPORTS_FURTHER_RESEARCH", "MIXED", "INSUFFICIENT_EVIDENCE"
]
DataQuality = Literal["complete", "partial", "insufficient"]


def _bounded_text(value: object, limit: int) -> str:
    """Keep public response strings within their documented Pydantic bounds."""
    text = str(value or "")
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}…"


class EvidenceItem(BaseModel):
    """Provider-neutral evidence envelope returned by Discovery and Analysis."""

    source: str = Field(min_length=1, max_length=120)
    url: Optional[str] = Field(None, max_length=2048)
    status: SourceStatus = "available"
    as_of: Optional[datetime] = None
    freshness: Freshness = "unknown"
    stance: EvidenceStance = "neutral"
    summary: str = Field(default="", max_length=1000)
    warning: Optional[str] = Field(None, max_length=500)


def research_contract_from_outputs(result: dict) -> dict:
    """Normalize legacy specialist outputs into the additive evidence contract."""
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    supporting: list[dict] = []
    contradicting: list[dict] = []
    missing: list[dict] = []
    for source, key in (
        ("Technical market data", "technical_output"),
        ("Company fundamentals", "fundamental_output"),
        ("News and sentiment", "sentiment_output"),
        ("Chart patterns", "chart_pattern_output"),
    ):
        output = result.get(key) or {}
        envelope = output.get("source_status") or {}
        status = envelope.get("status", "available" if output else "unavailable")
        signal = str(output.get("signal", "HOLD")).upper()
        item = {
            "source": source,
            "url": envelope.get("url"),
            "status": status if status in {"available", "unavailable", "error"} else "error",
            "as_of": envelope.get("as_of") or now,
            "freshness": envelope.get("freshness", "recent" if output else "unknown"),
            "stance": "supporting" if signal == "BUY" else "contradicting" if signal == "SELL" else "neutral",
            "summary": _bounded_text(
                output.get("narrative") or envelope.get("warning") or f"{source} unavailable",
                1000,
            ),
            "warning": (
                _bounded_text(envelope.get("warning"), 500)
                if envelope.get("warning")
                else None
            ),
        }
        if item["status"] != "available":
            missing.append(item)
        elif item["stance"] == "contradicting":
            contradicting.append(item)
        else:
            supporting.append(item)

    errors = [str(error) for error in (result.get("errors") or []) if error]
    for error in errors:
        missing.append({
            "source": "Analysis pipeline",
            "status": "error",
            "as_of": now,
            "freshness": "unknown",
            "stance": "neutral",
            "summary": _bounded_text(error, 1000),
            "warning": _bounded_text(error, 500),
        })

    available_count = len(supporting) + len(contradicting)
    if available_count < 2:
        quality, posture = "insufficient", "INSUFFICIENT_EVIDENCE"
    elif missing:
        quality, posture = "partial", "MIXED"
    elif contradicting:
        quality, posture = "complete", "MIXED"
    else:
        quality, posture = "complete", "SUPPORTS_FURTHER_RESEARCH"
    confidence = result.get("final_recommendation", {}).get("confidence", 0)
    return {
        "schema_version": "2.0",
        "research_posture": posture,
        "supporting_evidence": supporting,
        "contradictory_evidence": contradicting,
        "missing_evidence": missing,
        "data_quality": quality,
        "confidence_explanation": f"{available_count}/4 specialist sources available; {len(missing)} degraded.",
        "generated_at": now,
        "confidence": 0 if quality == "insufficient" else confidence,
    }


# ══════════════════════════════════════════════════════════════
# DISCOVERY
# ══════════════════════════════════════════════════════════════

class DiscoveryRequest(BaseModel):
    """Optional overrides for the discovery scan filters.

    NOTE on limits (TEST_REPORT.md issue #3):
      - `enrichment_limit` caps the post-pipeline TradingView re-scan that fills
        in OHLCV/RSI/etc on the F1-bucketed symbols. Lower = faster, but more
        symbols fall back to sparse rows.
      - `per_bucket_limit` caps each SHORT/MID/LONG bucket *before* enrichment.
        This is what most callers want when they say "limit".
      - `limit` (legacy, deprecated) is kept as an alias for `enrichment_limit`
        so existing clients don't break.
    """
    min_market_cap: Optional[float] = Field(None, description="Minimum market cap in INR (e.g. 50000000000 for ₹5000 Cr)")
    min_relative_volume: Optional[float] = Field(None, description="Minimum relative volume vs 10D avg")
    rsi_min: Optional[float] = Field(None, description="Minimum RSI (14)")
    rsi_max: Optional[float] = Field(None, description="Maximum RSI (14)")
    limit: Optional[int] = Field(None, ge=1, le=200, description="DEPRECATED — alias for enrichment_limit")
    enrichment_limit: Optional[int] = Field(None, ge=1, le=200, description="Cap rows pulled by the post-pipeline TradingView re-scan")
    per_bucket_limit: Optional[int] = Field(None, ge=1, le=50, description="Cap stocks returned per horizon bucket (SHORT/MID/LONG)")
    horizon: Optional[str] = Field(None, description="Filter results to a single horizon: SHORT/MID/LONG")
    use_cache: Optional[bool] = Field(False, description="If true and cache is fresh, return cached F1 result (instant)")


class PriceTargets(BaseModel):
    """ATR-based quick price targets for a discovered stock."""
    buy_price: Optional[float] = Field(None, description="Suggested entry/buy price (₹)")
    target_price: Optional[float] = Field(None, description="ATR-based target price (₹)")
    stop_loss: Optional[float] = Field(None, description="ATR-based stop-loss price (₹)")
    risk_reward: Optional[float] = Field(None, description="Risk-to-reward ratio")
    suggested_duration: Optional[str] = Field(None, description="Suggested holding period")


class ScreeningData(BaseModel):
    """Raw screening criteria from TradingView scan — real computed values, not LLM estimates."""
    rsi: float | None = None
    pe_ratio: float | None = None
    roe: float | None = None
    market_cap: float | None = None
    relative_volume: float | None = None
    ema20: float | None = None
    ema50: float | None = None
    ema200: float | None = None
    atr: float | None = None
    debt_to_equity: float | None = None
    net_margin: float | None = None
    perf_week: float | None = None
    perf_1m: float | None = None
    perf_3m: float | None = None


class DiscoveredStock(BaseModel):
    """A single stock from the discovery scan, F1-tagged with a horizon."""
    symbol: str
    close: Optional[float] = None
    change_pct: Optional[float] = None
    volume: Optional[int] = None
    relative_volume: Optional[float] = None
    rsi: Optional[float] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    roe: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None

    # ── F1 horizon classification ─────────────────────────────
    horizon: Optional[str] = Field(None, description="SHORT / MID / LONG (AI-tagged by Stage 8)")
    discovery_score: Optional[int] = Field(None, description="0-100 conviction score within horizon bucket")
    confidence: Optional[int] = Field(None, description="Confidence / probability score")
    rank: Optional[int] = Field(None, description="Rank within horizon bucket (1 = best)")
    catalyst: Optional[str] = Field(None, description="Specific event/trend that could move this stock")
    risk_flags: list[str] = Field(default_factory=list, description="Risk tags from F1 LLM")
    indicative_target: Optional[float] = Field(None, description="F1 rough target (NOT for trading)")
    suggested_hold_days: Optional[int] = None

    # ── Enrichments ───────────────────────────────────────────
    news_headlines: list[str] = Field(default_factory=list, description="Recent news headlines for the stock")
    price_targets: Optional[PriceTargets] = Field(None, description="ATR-based quick price targets")
    ai_reasoning: Optional[str] = Field(None, description="AI explanation of why this stock was selected")
    pick_type: Optional[str] = Field(None, description="Type of pick: Technical, Fundamental, or Both")
    holding_period: Optional[str] = Field(None, description="Suggested holding period")
    expected_return_pct: Optional[float] = Field(None, description="Expected return percentage to target")

    # ── Technical snapshot from screener ──────────────────────
    atr: Optional[float] = None
    ema20: Optional[float] = None
    ema50: Optional[float] = None
    ema200: Optional[float] = None
    perf_week: Optional[float] = None
    perf_1m: Optional[float] = None
    perf_3m: Optional[float] = None
    debt_to_equity: Optional[float] = None
    net_margin: Optional[float] = None
    price_book: Optional[float] = None
    dividend_yield: Optional[float] = None

    # ── Screening data + analysis tracking ────────────────────
    screening_data: ScreeningData | None = None
    analysis_status: str = "discovered"

    # ── F2 Analysis Status (populated on reload if analyzed) ──
    recommendation_id: Optional[str] = None
    recommendation: Optional[str] = None
    full_response: Optional[dict] = None

    # Additive OpenAI Build Week evidence contract.
    why_now: Optional[str] = None
    evidence: list[EvidenceItem] = Field(default_factory=list)
    data_quality: DataQuality = "partial"
    research_posture: ResearchPosture = "MIXED"

    @model_validator(mode="before")
    @classmethod
    def normalize_evidence_contract(cls, values):
        if not isinstance(values, dict):
            return values
        values = dict(values)
        values.setdefault("why_now", values.get("catalyst") or values.get("ai_reasoning"))
        evidence = values.get("evidence") or []
        if evidence and all(item.get("status") == "available" for item in evidence if isinstance(item, dict)):
            values.setdefault("data_quality", "complete")
        elif evidence and all(item.get("status") != "available" for item in evidence if isinstance(item, dict)):
            values["data_quality"] = "insufficient"
            values["research_posture"] = "INSUFFICIENT_EVIDENCE"
        else:
            values.setdefault("data_quality", "partial")
            values.setdefault("research_posture", "MIXED")
        return values


class DiscoveryResponse(BaseModel):
    """Response for the /discover endpoint — F1 final returns 3 horizon buckets."""
    run_id: str
    task: str = "discover"
    stocks_found: int
    stocks: list[DiscoveredStock]                       # flat list (legacy)
    buckets: dict = Field(default_factory=lambda: {"SHORT": [], "MID": [], "LONG": []},
                          description="F1 horizon buckets: {SHORT: [...], MID: [...], LONG: [...]}")
    macro_regime: str = "SIDEWAYS"
    market_pulse_score: int = 50
    economic_score: Optional[int] = None
    economic_regime: Optional[str] = None
    market_sentiment: Optional[float] = None
    hot_sectors: list[str] = []
    avoid_sectors: list[str] = []
    active_horizons: list[str] = Field(default_factory=lambda: ["SHORT", "MID", "LONG"])
    ai_summary: Optional[str] = Field(None, description="AI-generated summary of the market scan")
    errors: list[str] = []
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))


# ══════════════════════════════════════════════════════════════
# DIRECT ANALYSIS
# ══════════════════════════════════════════════════════════════

class AnalyzeRequest(BaseModel):
    """Request for analyzing a specific stock."""
    symbol: str = Field(..., description="Stock symbol, e.g. 'RELIANCE'")
    suggested_horizon: Optional[str] = Field(None, description="SHORT/MID/LONG inherited from F1; defaults to MID if absent")


class AgentSignals(BaseModel):
    """Individual signals from each worker agent (4 specialists)."""
    technical: str = "HOLD"
    fundamental: str = "HOLD"
    sentiment: str = "HOLD"
    chart_pattern: str = "HOLD"


class TechnicalSummary(BaseModel):
    """Summary of technical analysis output."""
    signal: str = "HOLD"
    confidence: float = 0.0
    narrative: str = ""
    key_levels: Optional[dict] = None
    current_price: Optional[float] = None
    atr: Optional[float] = None
    rsi: Optional[float] = None
    raw_data: Optional[dict] = None
    sub_scores: Optional[dict] = None


class FundamentalSummary(BaseModel):
    """Summary of fundamental analysis output."""
    signal: str = "HOLD"
    confidence: float = 0.0
    weighted_score: float = 0.0
    narrative: str = ""
    strengths: list[str] = []
    weaknesses: list[str] = []
    sub_scores: Optional[dict] = None


class SentimentSummary(BaseModel):
    """Summary of sentiment analysis output."""
    signal: str = "HOLD"
    confidence: float = 0.0
    aggregate_score: float = 0.0
    narrative: str = ""
    key_themes: list[str] = []
    anomaly_count: int = 0
    headline_count: int = 0
    fallback_used: bool = False
    headlines: list[dict] = []  # [{text, source, score}]
    sub_scores: Optional[dict] = None


class ChartPatternSummary(BaseModel):
    """Summary of chart pattern analysis output (F2 4th specialist)."""
    signal: str = "HOLD"
    confidence: float = 0.0
    narrative: str = ""
    patterns_detected: list[str] = []
    sub_scores: Optional[dict] = None


class DebateSummary(BaseModel):
    """Summary of debate agent output. F2 final: ALWAYS runs."""
    triggered: bool = True
    bull_case: Optional[str] = None
    bear_case: Optional[str] = None
    missed_risks: list[str] = []
    independent_signal: Optional[str] = None
    independent_confidence: Optional[float] = None
    agrees_with_consensus: Optional[bool] = None
    synthesis: Optional[str] = None
    evidence_citations: list[str] = []


class ValidatorIssue(BaseModel):
    """A single issue raised by the 3-Layer Validator."""
    layer: int
    field: str
    action: str          # "clamp" | "force_wait" | "dampen" | "reject"
    before: Optional[float] = None
    after: Optional[float] = None
    note: Optional[str] = None


class HorizonConfirmation(BaseModel):
    """Output of F2 Stage 2."""
    suggested_horizon: Optional[str] = None
    final_horizon: Optional[str] = None
    override_reason: Optional[str] = None
    horizon_scores: dict = Field(default_factory=dict)


class AnalyzeResponse(BaseModel):
    """Full response for the /analyze endpoint — F1/F2 final schema."""
    run_id: str
    symbol: str
    company_name: Optional[str] = None
    recommendation: str = "WAIT"        # BUY/SELL/WAIT (HOLD merged into WAIT)
    confidence: float = 0.0
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    risk_reward: Optional[float] = None
    upside_pct: Optional[float] = None
    risk_pct: Optional[float] = None
    profit_pct: Optional[float] = None
    timeframe: Optional[str] = None
    horizon_days: Optional[int] = None
    position_size_pct: Optional[float] = None
    narrative: str = ""
    key_risks: list[str] = []
    key_catalysts: list[str] = []
    agent_signals: AgentSignals = AgentSignals()
    technical_summary: Optional[TechnicalSummary] = None
    fundamental_summary: Optional[FundamentalSummary] = None
    sentiment_summary: Optional[SentimentSummary] = None
    chart_pattern_summary: Optional[ChartPatternSummary] = None
    debate_summary: Optional[DebateSummary] = None
    horizon_confirmation: Optional[HorizonConfirmation] = None
    validator_issues: list[ValidatorIssue] = []
    validator_status: str = "accepted"
    macro_regime: str = "SIDEWAYS"
    market_pulse_score: int = 50
    economic_score: Optional[int] = None
    economic_regime: Optional[str] = None
    horizon: Optional[str] = None                   # final horizon (SHORT/MID/LONG)
    recommendation_id: Optional[str] = None
    cost_per_analysis: Optional[float] = None       # USD
    cost_per_analysis_inr: Optional[float] = None  # INR
    errors: list[str] = []
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))

    # Additive, evidence-first public contract. Legacy fields above remain intact.
    schema_version: str = "2.0"
    research_posture: ResearchPosture = "MIXED"
    why_now: Optional[str] = None
    initial_thesis: Optional[str] = None
    final_thesis: Optional[str] = None
    supporting_evidence: list[EvidenceItem] = Field(default_factory=list)
    contradictory_evidence: list[EvidenceItem] = Field(default_factory=list)
    missing_evidence: list[EvidenceItem] = Field(default_factory=list)
    data_quality: DataQuality = "partial"
    confidence_explanation: Optional[str] = None
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    model: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_research_posture(cls, values):
        if not isinstance(values, dict):
            return values
        values = dict(values)
        values.setdefault("why_now", values.get("f1_catalyst"))
        values.setdefault("final_thesis", values.get("narrative"))
        errors = [str(error) for error in (values.get("errors") or []) if error]
        available = len(values.get("supporting_evidence") or []) + len(values.get("contradictory_evidence") or [])
        if errors and not available:
            values["missing_evidence"] = values.get("missing_evidence") or [
                {
                    "source": "analysis pipeline",
                    "status": "unavailable",
                    "freshness": "unknown",
                    "stance": "neutral",
                    "summary": _bounded_text(error, 1000),
                    "warning": _bounded_text(error, 500),
                }
                for error in errors[:10]
            ]
            values["data_quality"] = "insufficient"
            values["research_posture"] = "INSUFFICIENT_EVIDENCE"
            values["confidence"] = 0
        elif available:
            has_contradiction = bool(values.get("contradictory_evidence"))
            values.setdefault("data_quality", "partial" if errors else "complete")
            values.setdefault(
                "research_posture",
                "MIXED" if has_contradiction else "SUPPORTS_FURTHER_RESEARCH",
            )
        return values


# ══════════════════════════════════════════════════════════════
# MARKET CONTEXT  (GET /analysis/context/today)
# ══════════════════════════════════════════════════════════════
# Real-or-null contract: economic / market_pulse / macro_context are persisted
# in DB and returned with real values. news + planner are LLM-generated per F1
# run and NOT persisted anywhere yet, so they are Optional and come back null
# until F1 persistence is added. Sub-fields that have no DB source are Optional
# so we never fabricate them. See the `source` flag on MarketContextResponse.

class EconomicContextSchema(BaseModel):
    score: Optional[int] = None
    regime: Optional[str] = None  # EXPANSION | STABLE | SLOWING | CONTRACTION
    # Not persisted today → Optional, returned empty until a source exists
    positives: List[str] = []
    risks: List[str] = []
    overweight_sectors: List[str] = []
    underweight_sectors: List[str] = []
    reasoning: Optional[str] = None
    model_used: Optional[str] = None
    built_at: Optional[str] = None


class SectorStrengthItem(BaseModel):
    sector: str
    rank: int


class MarketPulseSchema(BaseModel):
    score: Optional[int] = None
    regime: Optional[str] = None  # BULL | SIDEWAYS | BEAR | CRISIS
    india_vix: Optional[float] = None
    nifty_level: Optional[float] = None
    advance_decline_ratio: Optional[float] = None
    sector_strength: List[SectorStrengthItem] = []   # not persisted → empty today
    breadth_signal: Optional[str] = None  # HEALTHY | DETERIORATING | COLLAPSED (derived)
    market_health: Optional[str] = None   # STRONG | MODERATE | WEAK | FRAGILE (derived)
    reasoning: Optional[str] = None


class NewsContextSchema(BaseModel):
    """LLM-generated by the F1 news node; NOT persisted yet — whole block is null."""
    market_sentiment: float  # -1..+1
    hot_sectors: List[str]
    avoid_sectors: List[str]
    anomaly_alerts: List[str]
    reasoning: str
    model_used: str


class MacroContextSchema(BaseModel):
    regime: Optional[str] = None  # BULL | SIDEWAYS | BEAR | CRISIS
    confidence: Optional[float] = None
    triggers: Dict[str, str] = {}
    reasoning: Optional[str] = None  # not persisted today
    model_used: Optional[str] = None


class HorizonPlanDetails(BaseModel):
    agent_weights: Dict[str, float]
    min_conviction: int
    strategy: str


class PlannerContextSchema(BaseModel):
    """LLM-generated by the F1 planner node; NOT persisted yet — whole block is null."""
    active_horizons: List[str]
    overall_caution: str  # NORMAL | CAUTIOUS | ELEVATED | CRISIS
    horizon_plans: Dict[str, HorizonPlanDetails]
    reasoning: str


class MarketContextResponse(BaseModel):
    date: str
    # "db" = every section backed by real data; "partial" = some sections null
    # because they aren't persisted yet (news / planner).
    source: str = "partial"
    economic: EconomicContextSchema
    market_pulse: MarketPulseSchema
    news: Optional[NewsContextSchema] = None
    macro_context: MacroContextSchema
    planner: Optional[PlannerContextSchema] = None

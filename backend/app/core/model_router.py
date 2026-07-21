"""Provider boundary for OpenAI GPT-5.6 models.

The rest of the graph intentionally keeps the LangChain ``invoke``/``ainvoke``
contract. Client construction is lazy so imports and hermetic tests do not need
an API key; the key is read only from the runtime environment.
"""

import contextvars
from enum import Enum
from typing import Optional

from app.core.config import logger, settings


_token_acc: "contextvars.ContextVar[dict | None]" = contextvars.ContextVar(
    "_token_acc", default=None
)


def reset_token_accumulator() -> None:
    _token_acc.set({"input": 0, "output": 0})


def read_token_accumulator() -> dict:
    acc = _token_acc.get()
    return dict(acc) if acc else {"input": 0, "output": 0}


def _add_tokens(tokens_in: int, tokens_out: int) -> None:
    acc = _token_acc.get()
    if acc is not None:
        acc["input"] += int(tokens_in or 0)
        acc["output"] += int(tokens_out or 0)


try:
    from langchain_core.callbacks.base import BaseCallbackHandler

    class TokenUsageCollector(BaseCallbackHandler):
        def on_llm_end(self, response, **kwargs):
            try:
                usage = (getattr(response, "llm_output", None) or {}).get(
                    "token_usage", {}
                )
                tokens_in = usage.get("prompt_tokens", usage.get("input_tokens", 0))
                tokens_out = usage.get("completion_tokens", usage.get("output_tokens", 0))
                if not (tokens_in or tokens_out):
                    for generations in getattr(response, "generations", None) or []:
                        for generation in generations:
                            metadata = getattr(
                                getattr(generation, "message", None), "usage_metadata", None
                            ) or {}
                            tokens_in += metadata.get("input_tokens", 0) or 0
                            tokens_out += metadata.get("output_tokens", 0) or 0
                _add_tokens(tokens_in, tokens_out)
            except Exception:
                pass

    _TOKEN_COLLECTOR = TokenUsageCollector()
except Exception:
    _TOKEN_COLLECTOR = None


class ModelTier(str, Enum):
    """Workload roles, independent of any provider's product naming."""

    DISCOVERY = "discovery"
    ANALYSIS = "analysis"
    ANALYSIS_DEEP = "analysis_deep"


APPROVED_MODEL_IDS = frozenset({"gpt-5.6-sol", "gpt-5.6-terra"})
APPROVED_REASONING_EFFORTS = frozenset({"none", "low", "medium", "high", "xhigh", "max"})


def validate_model_id(model_id: str) -> str:
    """Return a normalized approved model id or fail before any API request."""
    normalized = (model_id or "").strip().lower()
    if normalized not in APPROVED_MODEL_IDS:
        approved = ", ".join(sorted(APPROVED_MODEL_IDS))
        raise ValueError(f"Unsupported OpenAI model '{model_id}'. Approved models: {approved}.")
    return normalized


def validate_reasoning_effort(reasoning_effort: str) -> str:
    normalized = (reasoning_effort or "").strip().lower()
    if normalized not in APPROVED_REASONING_EFFORTS:
        approved = ", ".join(sorted(APPROVED_REASONING_EFFORTS))
        raise ValueError(
            f"Unsupported OpenAI reasoning effort '{reasoning_effort}'. "
            f"Approved values: {approved}."
        )
    return normalized


def _configured_model_id(tier: ModelTier) -> str:
    role = ModelTier(tier)
    configured = {
        ModelTier.DISCOVERY: settings.OPENAI_DISCOVERY_MODEL,
        ModelTier.ANALYSIS: settings.OPENAI_ANALYSIS_MODEL,
        ModelTier.ANALYSIS_DEEP: settings.OPENAI_ANALYSIS_MODEL,
    }[role]
    return validate_model_id(configured)


def _configured_reasoning_effort(tier: ModelTier) -> str:
    role = ModelTier(tier)
    configured = {
        ModelTier.DISCOVERY: settings.OPENAI_DISCOVERY_REASONING_EFFORT,
        ModelTier.ANALYSIS: settings.OPENAI_ANALYSIS_REASONING_EFFORT,
        ModelTier.ANALYSIS_DEEP: settings.OPENAI_DEEP_REASONING_EFFORT,
    }[role]
    return validate_reasoning_effort(configured)


class OpenAIChatAdapter:
    """Small lazy adapter preserving LangChain's sync/async call surface."""

    def __init__(self, model_id: str, reasoning_effort: str = "low", json_mode: bool = False):
        self.model_id = validate_model_id(model_id)
        self.reasoning_effort = validate_reasoning_effort(reasoning_effort)
        self.json_mode = json_mode
        self._client = None

    def _client_instance(self):
        if self._client is not None:
            return self._client
        if not settings.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured. Supply it at runtime to use GPT-5.6."
            )

        from langchain_openai import ChatOpenAI

        if "use_responses_api" not in getattr(ChatOpenAI, "model_fields", {}):
            raise RuntimeError(
                "Installed langchain-openai does not support the Responses API. "
                "Install the version declared in requirements.txt."
            )

        kwargs = {
            "model": self.model_id,
            "api_key": settings.OPENAI_API_KEY,
            "max_retries": 2,
            "timeout": settings.OPENAI_REQUEST_TIMEOUT_SECONDS,
            "reasoning_effort": self.reasoning_effort,
            "use_responses_api": True,
        }
        if _TOKEN_COLLECTOR is not None:
            kwargs["callbacks"] = [_TOKEN_COLLECTOR]
        if self.json_mode:
            # ChatOpenAI translates this JSON-object contract to Responses API
            # ``text.format`` while retaining Chat Completions compatibility.
            kwargs["model_kwargs"] = {
                "response_format": {"type": "json_object"}
            }
        self._client = ChatOpenAI(**kwargs)
        return self._client

    def invoke(self, input, config=None, **kwargs):
        return self._client_instance().invoke(input, config=config, **kwargs)

    async def ainvoke(self, input, config=None, **kwargs):
        return await self._client_instance().ainvoke(input, config=config, **kwargs)

    def __getattr__(self, name):
        # Preserve infrequently used LangChain helpers without eagerly creating
        # a client during imports.
        return getattr(self._client_instance(), name)


def get_model(
    tier: ModelTier,
    json_mode: bool = False,
    custom_key: Optional[str] = None,
    custom_model: Optional[str] = None,
):
    if custom_key:
        raise ValueError("Client-supplied API keys are not supported.")
    role = ModelTier(tier)
    model_id = validate_model_id(custom_model) if custom_model else _configured_model_id(role)
    return OpenAIChatAdapter(
        model_id=model_id,
        reasoning_effort=_configured_reasoning_effort(role),
        json_mode=json_mode,
    )


def get_model_id(tier: ModelTier) -> str:
    return _configured_model_id(tier)


def get_model_metadata() -> dict:
    """Public, secret-free provider metadata for diagnostics and health checks."""
    return {
        "provider": "openai",
        "transport": "responses",
        "models": {
            "discovery": get_model_id(ModelTier.DISCOVERY),
            "analysis": get_model_id(ModelTier.ANALYSIS),
            "analysis_deep": get_model_id(ModelTier.ANALYSIS_DEEP),
        },
        "reasoning_effort": {
            "discovery": _configured_reasoning_effort(ModelTier.DISCOVERY),
            "analysis": _configured_reasoning_effort(ModelTier.ANALYSIS),
            "analysis_deep": _configured_reasoning_effort(ModelTier.ANALYSIS_DEEP),
        },
    }


# Official standard text-token prices, expressed per token (July 2026).
COST_RATES_USD = {
    "gpt-5.6-sol": {"input": 5.00 / 1_000_000, "output": 30.00 / 1_000_000},
    "gpt-5.6-terra": {"input": 2.50 / 1_000_000, "output": 15.00 / 1_000_000},
}
USD_TO_INR_FALLBACK = 84.0


def compute_cost(model_id: str, tokens_in: int, tokens_out: int) -> float:
    rates = COST_RATES_USD[validate_model_id(model_id)]
    return round(tokens_in * rates["input"] + tokens_out * rates["output"], 8)


def cost_usd_to_inr(cost_usd: float, usd_inr: float = USD_TO_INR_FALLBACK) -> float:
    return round(cost_usd * usd_inr, 4)

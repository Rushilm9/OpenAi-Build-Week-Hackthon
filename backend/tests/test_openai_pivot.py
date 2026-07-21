import os
import asyncio
import json
from pathlib import Path
import subprocess
import sys
import types

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


def test_model_tiers_are_provider_neutral_and_map_to_explicit_gpt56_roles():
    from app.core.model_router import ModelTier, get_model_id

    assert {tier.name for tier in ModelTier} == {
        "DISCOVERY",
        "ANALYSIS",
        "ANALYSIS_DEEP",
    }
    assert get_model_id(ModelTier.DISCOVERY) == "gpt-5.6-terra"
    assert get_model_id(ModelTier.ANALYSIS) == "gpt-5.6-sol"
    assert get_model_id(ModelTier.ANALYSIS_DEEP) == "gpt-5.6-sol"


def test_model_tiers_follow_configured_openai_models(monkeypatch):
    from app.core import model_router

    monkeypatch.setattr(
        model_router.settings, "OPENAI_ANALYSIS_MODEL", "gpt-5.6-terra"
    )
    monkeypatch.setattr(
        model_router.settings, "OPENAI_DISCOVERY_MODEL", "gpt-5.6-sol"
    )

    assert model_router.get_model_id(model_router.ModelTier.ANALYSIS) == "gpt-5.6-terra"
    assert model_router.get_model_id(model_router.ModelTier.ANALYSIS_DEEP) == "gpt-5.6-terra"
    assert model_router.get_model_id(model_router.ModelTier.DISCOVERY) == "gpt-5.6-sol"


def test_environment_model_overrides_reach_router():
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": "sqlite:///:memory:",
            "OPENAI_ANALYSIS_MODEL": "gpt-5.6-terra",
            "OPENAI_DISCOVERY_MODEL": "gpt-5.6-sol",
        }
    )
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from app.core.model_router import ModelTier, get_model_id; "
                "print('MODEL_OVERRIDE=' + get_model_id(ModelTier.ANALYSIS) + ',' + "
                "get_model_id(ModelTier.DISCOVERY))"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert "MODEL_OVERRIDE=gpt-5.6-terra,gpt-5.6-sol" in probe.stdout


@pytest.mark.parametrize("entrypoint", ["get_model_id", "get_model"])
@pytest.mark.parametrize("configured_model", ["gpt-4o", "gemini-2.5-pro", ""])
def test_configured_models_are_centrally_validated(monkeypatch, entrypoint, configured_model):
    from app.core import model_router

    monkeypatch.setattr(
        model_router.settings, "OPENAI_DISCOVERY_MODEL", configured_model
    )

    with pytest.raises(ValueError, match="approved|supported"):
        getattr(model_router, entrypoint)(model_router.ModelTier.DISCOVERY)


def test_custom_model_uses_the_same_allowlist_and_custom_keys_are_rejected():
    from app.core.model_router import ModelTier, get_model

    assert get_model(ModelTier.DISCOVERY, custom_model="gpt-5.6-sol").model_id == "gpt-5.6-sol"
    with pytest.raises(ValueError, match="approved|supported"):
        get_model(ModelTier.DISCOVERY, custom_model="gpt-4o")
    with pytest.raises(ValueError, match="Client-supplied API keys"):
        get_model(ModelTier.DISCOVERY, custom_key="not-allowed")


def test_model_tiers_apply_reasoning_policy_and_require_responses_api(monkeypatch):
    from app.core import model_router

    captured = []

    class FakeChatOpenAI:
        model_fields = {
            "reasoning_effort": object(),
            "use_responses_api": object(),
        }

        def __init__(self, **kwargs):
            captured.append(kwargs)

    fake_module = types.ModuleType("langchain_openai")
    fake_module.ChatOpenAI = FakeChatOpenAI
    monkeypatch.setitem(sys.modules, "langchain_openai", fake_module)
    monkeypatch.setattr(model_router.settings, "OPENAI_API_KEY", "test-key")

    expected = {
        model_router.ModelTier.DISCOVERY: "low",
        model_router.ModelTier.ANALYSIS: "medium",
        model_router.ModelTier.ANALYSIS_DEEP: "high",
    }
    for tier, effort in expected.items():
        model_router.get_model(tier)._client_instance()
        assert captured[-1]["reasoning_effort"] == effort
        assert captured[-1]["use_responses_api"] is True


@pytest.mark.parametrize(
    ("setting_name", "tier"),
    [
        ("OPENAI_DISCOVERY_REASONING_EFFORT", "DISCOVERY"),
        ("OPENAI_ANALYSIS_REASONING_EFFORT", "ANALYSIS"),
        ("OPENAI_DEEP_REASONING_EFFORT", "ANALYSIS_DEEP"),
    ],
)
def test_reasoning_effort_overrides_are_configurable_and_validated(
    monkeypatch, setting_name, tier
):
    from app.core import model_router

    monkeypatch.setattr(model_router.settings, setting_name, "xhigh")
    adapter = model_router.get_model(getattr(model_router.ModelTier, tier))
    assert adapter.reasoning_effort == "xhigh"

    monkeypatch.setattr(model_router.settings, setting_name, "extreme")
    with pytest.raises(ValueError, match="reasoning effort"):
        model_router.get_model(getattr(model_router.ModelTier, tier))


def test_missing_responses_api_support_fails_fast(monkeypatch):
    from app.core import model_router

    class IncompatibleChatOpenAI:
        model_fields = {"reasoning_effort": object()}

        def __init__(self, **_kwargs):
            raise AssertionError("An incompatible client must not be constructed")

    fake_module = types.ModuleType("langchain_openai")
    fake_module.ChatOpenAI = IncompatibleChatOpenAI
    monkeypatch.setitem(sys.modules, "langchain_openai", fake_module)
    monkeypatch.setattr(model_router.settings, "OPENAI_API_KEY", "test-key")

    adapter = model_router.get_model(model_router.ModelTier.DISCOVERY)
    with pytest.raises(RuntimeError, match="Responses API"):
        adapter._client_instance()


def test_model_adapter_is_lazy_and_no_key_fails_before_client_import(monkeypatch):
    from app.core import model_router

    monkeypatch.setattr(model_router.settings, "OPENAI_API_KEY", "")
    monkeypatch.delitem(sys.modules, "langchain_openai", raising=False)

    adapter = model_router.get_model(model_router.ModelTier.DISCOVERY)
    assert adapter._client is None
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        adapter._client_instance()


def test_official_gpt56_cost_rates_are_used():
    from app.core.model_router import COST_RATES_USD, compute_cost

    assert COST_RATES_USD == {
        "gpt-5.6-sol": {"input": 5.0 / 1_000_000, "output": 30.0 / 1_000_000},
        "gpt-5.6-terra": {"input": 2.5 / 1_000_000, "output": 15.0 / 1_000_000},
    }
    assert compute_cost("gpt-5.6-sol", 1_000_000, 1_000_000) == 35.0
    assert compute_cost("gpt-5.6-terra", 1_000_000, 1_000_000) == 17.5


def test_openai_health_metadata_is_hermetic_and_never_exposes_a_key(monkeypatch):
    from app.core import config

    def fail_network(*_args, **_kwargs):
        raise AssertionError("Health metadata must not perform a network request")

    monkeypatch.setattr(config.settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr("socket.create_connection", fail_network)
    metadata = config.get_llm_info()
    encoded = json.dumps(metadata).lower()

    assert metadata["provider"] == "openai"
    assert metadata["discovery_model"] == config.settings.OPENAI_DISCOVERY_MODEL
    assert metadata["analysis_model"] == config.settings.OPENAI_ANALYSIS_MODEL
    assert metadata["analysis_deep_model"] == config.settings.OPENAI_ANALYSIS_MODEL
    assert metadata["status"] == "missing_key"
    assert "api_key" not in encoded
    assert "gemini" not in encoded


def test_phoenix_prompt_defaults_are_openai(monkeypatch):
    from app.core.phoenix_mcp import PhoenixMCP
    from app.core.config import settings

    calls = []
    client = PhoenixMCP()

    async def fake_call_tool(name, args):
        calls.append((name, args))
        return {"ok": True}

    monkeypatch.delenv("LLM_MODEL_NAME", raising=False)
    monkeypatch.setattr(client, "call_tool", fake_call_tool)
    asyncio.run(client.create_prompt(name="prompt", template="text", description="test"))

    assert calls[0][0] == "upsert-prompt"
    assert calls[0][1]["model_provider"] == "OPENAI"
    assert calls[0][1]["model_name"] == settings.OPENAI_ANALYSIS_MODEL

    with pytest.raises(ValueError, match="OPENAI"):
        asyncio.run(
            client.create_prompt(
                name="prompt",
                template="text",
                description="test",
                model_provider="GOOGLE",
            )
        )


def test_backend_source_and_requirements_have_no_google_llm_or_legacy_tiers():
    root = Path(__file__).resolve().parents[1]
    source = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in (root / "app").rglob("*.py")
    )
    requirements = (root / "requirements.txt").read_text(
        encoding="utf-8", errors="replace"
    )
    forbidden_source = (
        "gemini",
        "vertex ai",
        "vertexai",
        "chatvertex",
        "langchain_google",
        "google.generativeai",
        "generativelanguage.googleapis.com",
        "google_api_key",
        "google_cloud_project",
        "google_cloud_location",
        "use_vertex",
    )
    forbidden_requirements = (
        "google-generativeai",
        "google-genai",
        "langchain-google",
        "google-cloud-aiplatform",
        "vertex ai",
    )

    lowered_source = source.lower()
    lowered_requirements = requirements.lower()
    assert not [term for term in forbidden_source if term in lowered_source]
    assert not [term for term in forbidden_requirements if term in lowered_requirements]
    assert not any(
        legacy in source
        for legacy in (
            "ModelTier.FLASH_LITE",
            "ModelTier.FLASH",
            "ModelTier.PRO_THINK",
            "ModelTier.PRO",
        )
    )


def test_discovery_logs_configured_model_without_stale_provider_label(monkeypatch):
    from app.agents.discovery import node as discovery
    from app.core import model_router

    class FakeLLM:
        def invoke(self, _messages):
            return object()

    rows = []
    monkeypatch.setattr(
        model_router.settings, "OPENAI_DISCOVERY_MODEL", "gpt-5.6-sol"
    )
    monkeypatch.setattr(discovery, "get_model", lambda *_args, **_kwargs: FakeLLM())
    monkeypatch.setattr(
        discovery,
        "extract_content",
        lambda _response: '{"buckets":{"SHORT":[],"MID":[],"LONG":[]}}',
    )
    monkeypatch.setattr(discovery, "log_agent_run", lambda **kwargs: rows.append(kwargs))

    discovery._classify_and_rank(
        stock_data=[{"clean_symbol": "TEST", "close": 100}],
        regime="SIDEWAYS",
        active_horizons=["SHORT"],
        hot_sectors=[],
        avoid_sectors=[],
        economic_regime="STABLE",
        run_id="run-model-label",
    )

    assert rows[0]["model_used"] == "gpt-5.6-sol"
    assert "gemini" not in rows[0]["model_used"].lower()


def test_public_market_context_uses_configured_model_roles(monkeypatch):
    from app.api.routes import analysis
    from app.core import model_router
    from app.services import discovery_persist

    economic_snapshot = types.SimpleNamespace(
        economic_score=50,
        economic_regime="STABLE",
        llm_analysis=None,
        created_at=None,
        advance_decline_ratio=None,
        india_vix=None,
        nifty_level=None,
    )

    class EmptyQuery:
        def __init__(self, row=None):
            self.row = row

        def filter(self, *_args):
            return self

        def order_by(self, *_args):
            return self

        def first(self):
            return self.row

    class EmptySession:
        def query(self, model):
            row = economic_snapshot if model.__name__ == "EconomicSnapshots" else None
            return EmptyQuery(row)

        def close(self):
            pass

    monkeypatch.setattr(
        model_router.settings, "OPENAI_DISCOVERY_MODEL", "gpt-5.6-sol"
    )
    monkeypatch.setattr(
        model_router.settings, "OPENAI_ANALYSIS_MODEL", "gpt-5.6-terra"
    )
    monkeypatch.setattr(analysis, "SessionLocal", EmptySession)
    monkeypatch.setattr(
        discovery_persist,
        "load_last_discovery_context",
        lambda: {
            "economic_score": 50,
            "economic_regime": "STABLE",
            "market_sentiment": 0,
            "macro_regime": "SIDEWAYS",
        },
    )

    response = analysis.get_market_context_today()

    assert response.economic.model_used == "gpt-5.6-sol"
    assert response.news.model_used == "gpt-5.6-sol"
    assert response.macro_context.model_used == "gpt-5.6-terra"
    assert "gemini" not in response.model_dump_json().lower()


def test_json_mode_forwards_json_object_contract_and_preserves_invocation(monkeypatch):
    from app.core import model_router

    captured = {}

    class FakeChatOpenAI:
        model_fields = {
            "reasoning_effort": object(),
            "use_responses_api": object(),
        }

        def __init__(self, **kwargs):
            captured.update(kwargs)

        def invoke(self, input, config=None, **kwargs):
            return ("sync", input, config, kwargs)

        async def ainvoke(self, input, config=None, **kwargs):
            return ("async", input, config, kwargs)

    fake_module = types.ModuleType("langchain_openai")
    fake_module.ChatOpenAI = FakeChatOpenAI
    monkeypatch.setitem(sys.modules, "langchain_openai", fake_module)
    monkeypatch.setattr(model_router.settings, "OPENAI_API_KEY", "test-key")

    adapter = model_router.get_model(
        model_router.ModelTier.DISCOVERY, json_mode=True
    )

    assert adapter.invoke("prompt", config={"run": 1}, trace=True) == (
        "sync",
        "prompt",
        {"run": 1},
        {"trace": True},
    )
    assert asyncio.run(
        adapter.ainvoke("prompt", config={"run": 2}, trace=True)
    ) == ("async", "prompt", {"run": 2}, {"trace": True})
    assert captured["model_kwargs"]["response_format"] == {"type": "json_object"}
    assert captured["reasoning_effort"] == "low"
    assert captured["use_responses_api"] is True


def test_analysis_schema_normalizes_legacy_payload_to_insufficient_evidence():
    from app.schemas.analysis import AnalyzeResponse

    response = AnalyzeResponse(
        run_id="run-1",
        symbol="TEST",
        confidence=82,
        errors=["Fundamental data unavailable"],
    )

    assert response.data_quality == "insufficient"
    assert response.research_posture == "INSUFFICIENT_EVIDENCE"
    assert response.confidence == 0
    assert response.missing_evidence[0].status == "unavailable"
    assert response.schema_version == "2.0"


def test_discovery_schema_keeps_legacy_clients_working_with_evidence_defaults():
    from app.schemas.analysis import DiscoveredStock

    stock = DiscoveredStock(symbol="TEST", catalyst="Volume expansion")

    assert stock.why_now == "Volume expansion"
    assert stock.evidence == []
    assert stock.data_quality == "partial"
    assert stock.research_posture == "MIXED"


def test_dispatch_all_reused_results_still_finalizes(monkeypatch):
    from app.services import analysis_dispatcher as dispatcher

    dispatcher._status_store.clear()
    monkeypatch.setattr(
        dispatcher,
        "get_latest_recommendation_today",
        lambda symbol, horizon: {
            "recommendation_id": "rec-1",
            "recommendation": "WAIT",
            "confidence": 50,
            "horizon": horizon,
        },
    )
    completed = []

    dispatcher.dispatch_analysis(
        "run-reused",
        {"SHORT": [{"symbol": "TEST", "rank": 1}], "MID": [], "LONG": []},
        on_complete=lambda: completed.append(True),
    )

    assert completed == [True]
    assert dispatcher.get_status("run-reused")["complete"] is True


def test_unsafe_and_evaluation_routes_are_not_public():
    from app.main import app

    paths = {getattr(route, "path", None) for route in app.routes}
    assert "/analysis/reset" not in paths
    assert "/analysis/test-agent" not in paths
    assert "/api/evals/experiment" not in paths
    assert "/api/improve/propose" not in paths
    assert "/api/arize/eval-summary" not in paths


def test_news_sentiment_context_is_saved_in_durable_run_metadata():
    from app.services.discovery_persist import _run_context_from_result

    context = _run_context_from_result(
        {
            "market_sentiment": 0.0,
            "hot_sectors": ["IT"],
            "avoid_sectors": ["Realty"],
            "anomaly_alerts": ["Volatility spike"],
            "news_reasoning": "Mixed headlines produced a neutral score.",
            "discovered_buckets": {"SHORT": [{"symbol": "TEST"}]},
        }
    )

    assert context == {
        "market_sentiment": 0.0,
        "hot_sectors": ["IT"],
        "avoid_sectors": ["Realty"],
        "anomaly_alerts": ["Volatility spike"],
        "news_reasoning": "Mixed headlines produced a neutral score.",
    }
    assert "discovered_buckets" not in context


def test_news_sentiment_context_loads_from_latest_completed_run(monkeypatch):
    from app.services import discovery_persist

    expected = {
        "market_sentiment": -0.4,
        "hot_sectors": ["Pharma"],
        "news_reasoning": "Defensive sectors led the news cycle.",
    }

    class FakeQuery:
        def filter(self, *args):
            return self

        def order_by(self, *args):
            return self

        def first(self):
            return types.SimpleNamespace(workflow_config=expected)

    class FakeSession:
        closed = False

        def query(self, model):
            return FakeQuery()

        def close(self):
            self.closed = True

    session = FakeSession()
    monkeypatch.setattr(discovery_persist, "SessionLocal", lambda: session)
    monkeypatch.setattr(os.path, "exists", lambda path: False)

    assert discovery_persist.load_last_discovery_context() == expected
    assert session.closed is True

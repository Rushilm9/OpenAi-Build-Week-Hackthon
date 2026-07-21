from app.schemas.analysis import AnalyzeResponse, research_contract_from_outputs


def test_research_contract_bounds_long_specialist_narratives_before_response_validation():
    contract = research_contract_from_outputs(
        {
            "technical_output": {"signal": "BUY", "narrative": "T" * 1200},
            "fundamental_output": {"signal": "SELL", "narrative": "F" * 1200},
            "sentiment_output": {"signal": "HOLD", "narrative": "S" * 1200},
            "chart_pattern_output": {"signal": "HOLD", "narrative": "C" * 1200},
        }
    )

    response = AnalyzeResponse(run_id="run-1", symbol="HDFCBANK", **contract)

    evidence = response.supporting_evidence + response.contradictory_evidence
    assert evidence
    assert all(len(item.summary) <= 1000 for item in evidence)
    assert all(item.summary.endswith("…") for item in evidence)


def test_error_evidence_is_bounded_in_response_normalization():
    response = AnalyzeResponse(run_id="run-2", symbol="HDFCBANK", errors=["E" * 1200])

    item = response.missing_evidence[0]
    assert len(item.summary) == 1000
    assert len(item.warning or "") == 500
    assert item.summary.endswith("…")
    assert (item.warning or "").endswith("…")

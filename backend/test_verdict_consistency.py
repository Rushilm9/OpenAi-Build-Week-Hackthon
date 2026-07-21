"""
Unit tests for the single-source-of-truth verdict normalizer and the
narrative/verdict consistency guard.

Run:  python -m pytest test_verdict_consistency.py -v
(No DB / network required — pure functions only.)
"""

import pytest

from app.core.verdict import final_verdict, narrative_contradicts_verdict


# ── final_verdict() ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("raw,expected", [
    ("BUY", "BUY"),
    ("buy", "BUY"),
    (" Sell ", "SELL"),
    ("WAIT", "WAIT"),
    ("HOLD", "WAIT"),          # legacy HOLD collapses to WAIT
    ("hold", "WAIT"),
    ("", "WAIT"),
    (None, "WAIT"),
    ("garbage", "WAIT"),
])
def test_final_verdict_normalizes(raw, expected):
    assert final_verdict(raw) == expected


# ── narrative_contradicts_verdict() ──────────────────────────────────────────

def test_contradiction_buy_verdict_wait_prose():
    """The real production bug: verdict BUY, prose declares WAIT."""
    narrative = ("<ul><li>The final decision is to <b>WAIT</b>, overriding the "
                 "initial <b>BUY</b> recommendation. Confidence 71.4% exceeds the "
                 "70% cap.</li></ul>")
    assert narrative_contradicts_verdict(narrative, "BUY") is True


def test_no_contradiction_when_aligned_buy():
    narrative = ("<ul><li>The final decision is a <b>BUY</b> for SPIC, capped at "
                 "70% confidence due to conflicting signals.</li></ul>")
    assert narrative_contradicts_verdict(narrative, "BUY") is False


def test_no_contradiction_when_aligned_wait():
    narrative = ("<ul><li>The final decision is to <b>WAIT</b> on NFL with a "
                 "confidence of 66.5%.</li></ul>")
    assert narrative_contradicts_verdict(narrative, "WAIT") is False


def test_buy_narrative_may_mention_wait_word_without_contradiction():
    """A BUY narrative that merely *mentions* waiting is NOT a contradiction —
    only the declared 'final decision' clause counts."""
    narrative = ("<ul><li>The final decision is a <b>BUY</b>. We would otherwise "
                 "WAIT for a pullback, but momentum justifies entry now.</li></ul>")
    assert narrative_contradicts_verdict(narrative, "BUY") is False


def test_hold_in_prose_against_wait_verdict_is_not_contradiction():
    """Legacy HOLD in prose normalizes to WAIT — matches a WAIT verdict."""
    narrative = "<ul><li>The final decision is to <b>HOLD</b> for now.</li></ul>"
    assert narrative_contradicts_verdict(narrative, "WAIT") is False


def test_empty_or_unparseable_narrative_is_not_contradiction():
    assert narrative_contradicts_verdict("", "BUY") is False
    assert narrative_contradicts_verdict("Some prose with no decision clause.", "SELL") is False

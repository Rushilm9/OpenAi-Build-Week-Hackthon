"""
Sentiment Service — Wraps FinVADER for offline, free sentiment scoring fallback.
"""
import os
import tempfile
import nltk

# Ensure NLTK uses a writable directory (e.g. /tmp/nltk_data in read-only environments like Vercel)
_tmp_nltk_dir = os.environ.get("NLTK_DATA", os.path.join(tempfile.gettempdir(), "nltk_data"))
try:
    os.makedirs(_tmp_nltk_dir, exist_ok=True)
except Exception:
    pass

if _tmp_nltk_dir not in nltk.data.path:
    nltk.data.path.insert(0, _tmp_nltk_dir)
os.environ["NLTK_DATA"] = _tmp_nltk_dir

try:
    from finvader import finvader
    _FINVADER_AVAILABLE = True
except Exception as e:
    finvader = None
    _FINVADER_AVAILABLE = False
from app.core.config import logger

def score_headline(text: str) -> float:
    """
    Scores a financial text snippet using FinVADER.
    Returns:
        float: A composite sentiment score between -1.0 (extremely negative) and 1.0 (extremely positive).
    """
    if finvader is None:
        logger.warning("[yellow]FinVADER is not installed; skipping headline scoring[/yellow]")
        return 0.0
    try:
        try:
            score = finvader(text, indicator="compound", use_sentibignomics=True)
        except (TypeError, UnboundLocalError):
            try:
                score = finvader(text, indicator="compound", use_lm=True, use_vader=True)
            except Exception:
                score = finvader(text)
        return float(score)
        
    except Exception as e:
        logger.warning(f"[yellow]FinVADER scoring failed for text '{text[:20]}...': {e}[/yellow]")
        return 0.0

"""
LLM Singleton — backward-compat shim.
All agents should import from model_router instead:
    from app.core.model_router import get_model, ModelTier

get_llm() / get_json_llm() are kept so existing code doesn't break —
they delegate to the provider-neutral DISCOVERY role.
"""

from app.core.config import logger
from app.core.model_router import get_model, ModelTier


def get_llm():
    """Returns the high-throughput GPT-5.6 tier (backward compatibility)."""
    return get_model(ModelTier.DISCOVERY)


def get_json_llm():
    """Returns the high-throughput GPT-5.6 tier for JSON-oriented prompts."""
    return get_model(ModelTier.DISCOVERY, json_mode=True)


def log_llm_invocation(model_name: str, symbol: str, agent_name: str):
    logger.info(
        f"[bold magenta]LLM Invoked[/bold magenta] | "
        f"[cyan]{agent_name}[/cyan] | "
        f"Symbol: [bold white]{symbol}[/bold white] | "
        f"Model: [dim]{model_name}[/dim]"
    )


def extract_content(response) -> str:
    """
    Safely extract text from an LLM response.
    Responses-capable models can return response.content as content blocks
    instead of a plain string. This helper normalises both cases.
    """
    content = response.content
    if isinstance(content, list):
        # Join text parts from the list of content blocks
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(block.get("text", ""))
            else:
                parts.append(str(block))
        return "".join(parts).strip()
    return (content or "").strip()

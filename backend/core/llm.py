import httpx
import json
from core.config import settings


async def llm_generate(prompt: str, system: str = "") -> str:
    """
    Direct async call to Ollama /api/generate endpoint.
    Returns the generated text string.
    """
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
    except Exception as e:
        return f"[Rule-based classification]"


def llm_generate_sync(prompt: str, system: str = "") -> str:
    """Synchronous wrapper — used inside LangGraph nodes."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, llm_generate(prompt, system))
                return future.result()
        return loop.run_until_complete(llm_generate(prompt, system))
    except Exception:
        return "[Rule-based analysis]"

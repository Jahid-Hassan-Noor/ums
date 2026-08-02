import json
import logging
from urllib import error, request

from django.conf import settings


logger = logging.getLogger(__name__)


def _post_ollama_chat(model, messages):
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_ctx": 4096,
            },
        }
    ).encode("utf-8")
    req = request.Request(
        f"{settings.CHATBOT_OLLAMA_BASE_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=settings.CHATBOT_LLM_TIMEOUT_SECONDS) as response:
        data = json.loads(response.read().decode("utf-8"))
    return (data.get("message") or {}).get("content", "").strip()


def generate_chat_answer(messages):
    if not settings.CHATBOT_LLM_ENABLED:
        return None, "disabled"

    models = [settings.CHATBOT_MODEL, settings.CHATBOT_FAST_MODEL]
    seen = set()
    last_error = None
    for model in models:
        if not model or model in seen:
            continue
        seen.add(model)
        try:
            answer = _post_ollama_chat(model, messages)
            if answer:
                return answer, model
        except (OSError, error.URLError, error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            logger.warning("Chatbot model %s failed: %s", model, exc)
    return None, last_error or "unavailable"

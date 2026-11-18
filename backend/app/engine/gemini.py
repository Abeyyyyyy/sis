"""Klien Gemini lewat REST (tanpa SDK). Mengembalikan None bila kunci kosong atau panggilan gagal, supaya
engine otomatis memakai mode aturan."""
import json
import logging
import urllib.error
import urllib.request

from ..config import settings

log = logging.getLogger("uvicorn.error")
_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"


def enabled() -> bool:
    return bool(settings.gemini_api_key)


def generate(system: str, prompt: str, json_mode: bool = False, timeout: int = 25) -> str | None:
    if not enabled():
        return None
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0, **({"responseMimeType": "application/json"} if json_mode else {})},
    }
    req = urllib.request.Request(
        _URL.format(model=settings.gemini_model, key=settings.gemini_api_key),
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "ignore")[:300]
        log.warning("Gemini HTTP %s (model %s): %s", exc.code, settings.gemini_model, detail)
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError, OSError) as exc:
        log.warning("Gemini gagal (%s): %s", type(exc).__name__, exc)
    return None

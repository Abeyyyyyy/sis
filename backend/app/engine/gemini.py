"""Klien Gemini lewat REST (tanpa SDK). Mengembalikan None bila kunci kosong, sirkuit terbuka, atau panggilan gagal,
supaya engine otomatis memakai mode aturan.

Perbaikan: kunci API lewat header (bukan query string yang ikut tercatat di log/proxy), timeout lebih pendek,
dan circuit breaker agar Gemini yang down/lambat tidak membuat SETIAP request menunggu timeout dua kali."""
import json
import logging
import threading
import time
import urllib.error
import urllib.request

from ..config import settings

log = logging.getLogger("uvicorn.error")
_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

DEFAULT_TIMEOUT = 8          # detik, per panggilan (sebelumnya 25 x 2 panggilan per pertanyaan)
FAILURE_THRESHOLD = 3        # gagal beruntun sebelum sirkuit dibuka
COOLDOWN_SECONDS = 60        # lama Gemini dilewati saat sirkuit terbuka


class _Breaker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._fails = 0
        self._open_until = 0.0

    def allow(self) -> bool:
        with self._lock:
            return time.monotonic() >= self._open_until

    def ok(self) -> None:
        with self._lock:
            self._fails = 0

    def fail(self) -> None:
        with self._lock:
            self._fails += 1
            if self._fails >= FAILURE_THRESHOLD:
                self._open_until = time.monotonic() + COOLDOWN_SECONDS
                self._fails = 0
                log.warning("Gemini gagal %d kali beruntun; dilewati %d dtk (mode aturan).", FAILURE_THRESHOLD, COOLDOWN_SECONDS)


breaker = _Breaker()


def enabled() -> bool:
    return bool(settings.gemini_api_key)


def generate(system: str, prompt: str, json_mode: bool = False, timeout: int = DEFAULT_TIMEOUT) -> str | None:
    if not enabled() or not breaker.allow():
        return None
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0, **({"responseMimeType": "application/json"} if json_mode else {})},
    }
    req = urllib.request.Request(
        _URL.format(model=settings.gemini_model),
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": settings.gemini_api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        breaker.ok()
        return text
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "ignore")[:300]
        log.warning("Gemini HTTP %s (model %s): %s", exc.code, settings.gemini_model, detail)
        if exc.code == 429 or exc.code >= 500:  # galat 4xx lain = salah konfigurasi, bukan gangguan layanan
            breaker.fail()
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError, OSError) as exc:
        log.warning("Gemini gagal (%s): %s", type(exc).__name__, exc)
        breaker.fail()
    return None

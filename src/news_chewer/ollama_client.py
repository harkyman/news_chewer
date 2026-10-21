from typing import Any, Dict, Optional
import requests


class OllamaClient:
    """Minimal client for talking to a local Ollama HTTP endpoint.

    The exact Ollama HTTP API may vary between versions. This client sends a POST
    to `/api/generate` by default and returns the JSON response. Adjust as needed.
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    def generate(self, model: str, prompt: str, timeout: int = 90, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/generate"
        payload = {"model": "gemma2:latest", "prompt": prompt, "stream": False}
        if params:
            payload.update(params)
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        try:
            data = resp.json()
            return data.get("response", "")
        except Exception:
            return {"EXCEPTION: raw_text": resp.text}

import os
import json
import time
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List


def load_dotenv():
    """Lightweight pure-python .env loader."""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass


# Auto-load .env on import
load_dotenv()


class LLMClient:
    """
    Pluggable LLM Client supporting multiple providers:
    - Groq (llama-3.3-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768)
    - Google Gemini (gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash)
    - OpenAI (gpt-4o, gpt-4o-mini, etc.)
    - Anthropic (claude-3-5-sonnet, claude-3-haiku, etc.)
    - Ollama / Local HTTP endpoints
    - Local Deterministic Fallback Engine (no API key required)

    Improvements:
    2.3 — Gemini calls now use the dedicated systemInstruction field.
    2.4 — All HTTP calls retry up to MAX_RETRIES times with exponential backoff
          before falling through to the deterministic fallback.
    """

    MAX_RETRIES: int = 3       # maximum HTTP retry attempts
    RETRY_BASE_S: float = 1.0  # initial backoff delay in seconds

    def __init__(
        self,
        provider: str = "groq",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        self.provider = provider.lower().strip()
        self.model = model
        self.api_key = api_key
        self.api_base = api_base
        self._init_defaults()

    def _init_defaults(self):
        """Set default model names and read API keys from environment."""
        if not self.model:
            if self.provider in ("groq",):
                self.model = "llama-3.3-70b-versatile"
            elif self.provider in ("gemini", "google"):
                self.model = "gemini-3.6-flash"
            elif self.provider in ("openai", "chatgpt"):
                self.model = "gpt-4o-mini"
            elif self.provider in ("anthropic", "claude"):
                self.model = "claude-3-5-sonnet-20241022"
            elif self.provider in ("ollama", "local"):
                self.model = "llama3.2"
            else:
                self.model = "deterministic"

        if not self.api_key:
            if self.provider in ("groq",):
                self.api_key = os.getenv("GROQ_API_KEY")
            elif self.provider in ("gemini", "google"):
                self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            elif self.provider in ("openai", "chatgpt"):
                self.api_key = os.getenv("OPENAI_API_KEY")
            elif self.provider in ("anthropic", "claude"):
                self.api_key = os.getenv("ANTHROPIC_API_KEY")

    def set_api_key(self, api_key: str):
        """Update API key at runtime."""
        self.api_key = api_key

    def set_model(self, provider: str, model: Optional[str] = None, api_key: Optional[str] = None):
        """Switch model and provider at runtime."""
        self.provider = provider.lower().strip()
        self.model = model
        if api_key:
            self.api_key = api_key
        self._init_defaults()

    # ------------------------------------------------------------------
    # Public generation method
    # ------------------------------------------------------------------

    def generate_answer(self, prompt: str, system_instruction: str = "") -> str:
        """
        Sends generation request to the configured LLM provider.
        Falls back gracefully if API key is not configured or if all retries fail.
        """
        hosted_providers = ("groq", "gemini", "google", "openai", "chatgpt", "anthropic", "claude")
        if self.provider in hosted_providers and not self.api_key:
            return self._fallback_grounded_answer(prompt)

        try:
            if self.provider in ("groq",):
                return self._call_groq(prompt, system_instruction)
            elif self.provider in ("gemini", "google"):
                return self._call_gemini(prompt, system_instruction)
            elif self.provider in ("openai", "chatgpt"):
                return self._call_openai(prompt, system_instruction)
            elif self.provider in ("anthropic", "claude"):
                return self._call_anthropic(prompt, system_instruction)
            elif self.provider in ("ollama", "local"):
                return self._call_ollama(prompt, system_instruction)
            else:
                return self._fallback_grounded_answer(prompt)
        except Exception as e:
            return self._fallback_grounded_answer(prompt, error_msg=str(e))

    # ------------------------------------------------------------------
    # Internal HTTP helper with exponential-backoff retry (2.4)
    # ------------------------------------------------------------------

    def _http_post_with_retry(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        Sends a POST request and retries up to MAX_RETRIES times on transient errors
        (network issues, 5xx responses) using exponential backoff.
        4xx errors are NOT retried — the full JSON error body is surfaced immediately.
        """
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", **headers},
            method="POST",
        )
        last_exc: Optional[Exception] = None
        for attempt in range(self.MAX_RETRIES):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                # Read the full response body so the real reason is visible
                try:
                    body = e.read().decode("utf-8")
                    err_data = json.loads(body)
                    reason = err_data.get("error", {}).get("message", body)
                except Exception:
                    reason = str(e)
                rich_msg = f"HTTP Error {e.code}: {reason}"
                rich_exc = RuntimeError(rich_msg)
                # 4xx = client error — no point retrying; surface immediately
                if e.code < 500:
                    raise rich_exc
                last_exc = rich_exc
            except (urllib.error.URLError, OSError) as e:
                last_exc = e

            if attempt < self.MAX_RETRIES - 1:
                sleep_s = self.RETRY_BASE_S * (2 ** attempt)
                time.sleep(sleep_s)

        raise last_exc  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Provider-specific callers
    # ------------------------------------------------------------------

    def _call_groq(self, prompt: str, system_instruction: str) -> str:
        data = self._http_post_with_retry(
            url="https://api.groq.com/openai/v1/chat/completions",
            payload={
                "model": self.model or "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
            },
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        return data["choices"][0]["message"]["content"].strip()

    def _call_gemini(self, prompt: str, system_instruction: str) -> str:
        """
        2.3 — Uses the dedicated systemInstruction field for better model adherence.
        """
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload: Dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1024},
        }
        if system_instruction:
            payload["system_instruction"] = {"parts": [{"text": system_instruction}]}

        data = self._http_post_with_retry(url=url, payload=payload, headers={})
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    def _call_openai(self, prompt: str, system_instruction: str) -> str:
        data = self._http_post_with_retry(
            url="https://api.openai.com/v1/chat/completions",
            payload={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
            },
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        return data["choices"][0]["message"]["content"].strip()

    def _call_anthropic(self, prompt: str, system_instruction: str) -> str:
        data = self._http_post_with_retry(
            url="https://api.anthropic.com/v1/messages",
            payload={
                "model": self.model,
                "max_tokens": 1024,
                "system": system_instruction,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            },
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            timeout=30,
        )
        return data["content"][0]["text"].strip()

    def _call_ollama(self, prompt: str, system_instruction: str) -> str:
        base = self.api_base or "http://localhost:11434"
        data = self._http_post_with_retry(
            url=f"{base}/api/generate",
            payload={
                "model": self.model,
                "prompt": f"{system_instruction}\n\n{prompt}" if system_instruction else prompt,
                "stream": False,
            },
            headers={},
            timeout=45,
        )
        return data["response"].strip()

    # ------------------------------------------------------------------
    # Deterministic offline fallback
    # ------------------------------------------------------------------

    def _fallback_grounded_answer(self, prompt: str, error_msg: Optional[str] = None) -> str:
        """
        Deterministic Grounded Synthesis:
        Used when no API key is provided or when running in offline mode.
        """
        lines = prompt.strip().split("\n")
        context_blocks = [
            line for line in lines
            if line.startswith("• §") or line.startswith("• Amendment")
        ]

        if context_blocks:
            top_rule = context_blocks[0]
            answer = f"According to the applicable policy provisions:\n\n{top_rule}"
        else:
            answer = (
                "Based on the retrieved policy clauses, "
                "the rules are grounded in the cited sections below."
            )

        if error_msg:
            answer += f"\n\n[Note: Live API unavailable — {error_msg}]"

        return answer

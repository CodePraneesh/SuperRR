#!/usr/bin/env python3
"""
hf_inference_client.py
SupeRR Intelligence - Phase 4.4 Hugging Face Inference API Client

Integrates the official Hugging Face Serverless Inference API for Qwen/Qwen2.5-7B-Instruct.
Requirements:
- Read HF_TOKEN from environment (fallback: HUGGINGFACEHUB_API_TOKEN)
- Never log, expose, or hardcode API tokens
- Handle rate limits, network errors, timeouts, and model loading states
- Set configurable request timeouts
"""
import os
import time
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List
from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError


def _load_env_file():
    """Lightweight native loader for .env without requiring third-party dotenv."""
    candidates = [
        Path(".env"),
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parent.parent / ".env"
    ]
    for c in candidates:
        if c.exists():
            try:
                with open(c, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k and k not in os.environ:
                                os.environ[k] = v
                break
            except Exception:
                pass

_load_env_file()


class HFInferenceClient:
    """
    Client for Hugging Face Serverless Inference API.
    Calls Qwen/Qwen2.5-7B-Instruct with graceful error handling.
    """

    DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"

    def __init__(
        self,
        model: Optional[str] = None,
        token: Optional[str] = None,
        timeout: float = 25.0
    ):
        self.model = model or self.DEFAULT_MODEL
        # Read from environment securely; never hardcode
        self.token = token or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
        self.timeout = timeout
        self._client: Optional[InferenceClient] = None

        if self.token:
            try:
                self._client = InferenceClient(model=self.model, token=self.token, timeout=self.timeout)
            except Exception:
                self._client = None

    def is_configured(self) -> bool:
        """Returns True if a token is present and the client is initialized."""
        return bool(self.token and len(self.token.strip()) > 5)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.3
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Executes a grounded chat completion against Hugging Face.
        Returns:
            (success: bool, response_text: str, metadata: dict)
        """
        if not self.is_configured():
            return (
                False,
                "HF_TOKEN is not configured in the environment. Set HF_TOKEN to enable Tier 1 API generation.",
                {"error_type": "MISSING_TOKEN", "status_code": None, "model": self.model}
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        t0 = time.time()
        try:
            client = self._client or InferenceClient(model=self.model, token=self.token, timeout=self.timeout)
            response = client.chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            latency = round(time.time() - t0, 3)
            content = response.choices[0].message.content or ""

            return (
                True,
                content.strip(),
                {
                    "error_type": None,
                    "model": self.model,
                    "latency_sec": latency,
                    "finish_reason": response.choices[0].finish_reason
                }
            )

        except HfHubHTTPError as e:
            latency = round(time.time() - t0, 3)
            status_code = getattr(e.response, "status_code", None) if hasattr(e, "response") else None

            if status_code == 429:
                err_msg = "Hugging Face API rate limit reached (HTTP 429). Falling back to offline engine."
                err_type = "RATE_LIMIT"
            elif status_code == 503:
                err_msg = "Model currently loading or service unavailable (HTTP 503). Falling back to offline engine."
                err_type = "MODEL_UNAVAILABLE"
            elif status_code in (401, 403):
                err_msg = "Authentication error: HF_TOKEN is invalid or lacking permissions. Falling back to offline engine."
                err_type = "AUTH_ERROR"
            else:
                err_msg = f"Hugging Face HTTP Error ({status_code}): {str(e)[:150]}"
                err_type = f"HTTP_{status_code}"

            return (False, err_msg, {"error_type": err_type, "status_code": status_code, "latency_sec": latency})

        except TimeoutError:
            latency = round(time.time() - t0, 3)
            return (
                False,
                f"Request to Hugging Face timed out after {self.timeout}s. Falling back to offline engine.",
                {"error_type": "TIMEOUT", "status_code": 408, "latency_sec": latency}
            )

        except Exception as e:
            latency = round(time.time() - t0, 3)
            err_str = str(e)
            if "timeout" in err_str.lower():
                err_type = "TIMEOUT"
                msg = f"Request to Hugging Face timed out after {self.timeout}s."
            else:
                err_type = "NETWORK_ERROR"
                msg = f"Network connection error to Hugging Face: {err_str[:150]}"

            return (False, msg, {"error_type": err_type, "status_code": None, "latency_sec": latency})

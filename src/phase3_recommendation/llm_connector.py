"""
LLM Connector
==============
Unified API wrapper supporting multiple LLM providers:
- OpenAI (GPT-3.5 / GPT-4)
- Google Gemini
- Ollama (local models)

Handles edge cases:
- EC-3.1: LLM API Timeout
- EC-3.5: Rate limit exceeded
- EC-3.7: Provider switching / failover
- EC-3.9: Cost tracking for API calls
"""

import sys
import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.phase0.config import (
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    LLM_TIMEOUT_SECONDS,
    GROQ_API_KEY,
    GROQ_MODEL,
)

logger = logging.getLogger("recommendation.llm_connector")

# ---------------------------------------------------------------------------
# Cost estimation (approximate USD per 1K tokens)
# ---------------------------------------------------------------------------
COST_PER_1K_TOKENS = {
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gemini-pro": {"input": 0.0, "output": 0.0},  # Free tier
    "gemini-1.5-flash": {"input": 0.0, "output": 0.0},
    "llama3": {"input": 0.0, "output": 0.0},  # Local
    "llama3-70b-8192": {"input": 0.00059, "output": 0.00079}, # Groq
}


class LLMResponse:
    """Encapsulates the response from an LLM provider."""

    def __init__(
        self,
        content: str,
        provider: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: int = 0,
        estimated_cost_usd: float = 0.0,
        success: bool = True,
        error: str = "",
    ):
        self.content = content
        self.provider = provider
        self.model = model
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.latency_ms = latency_ms
        self.estimated_cost_usd = estimated_cost_usd
        self.success = success
        self.error = error


# ---------------------------------------------------------------------------
# Abstract Base Provider
# ---------------------------------------------------------------------------

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Send prompts to the LLM and return the response."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is configured and available."""
        pass


# ---------------------------------------------------------------------------
# OpenAI Provider
# ---------------------------------------------------------------------------

class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider."""

    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.model = OPENAI_MODEL
        self.provider_name = "openai"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key != "your-openai-api-key-here")

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)

            start_time = time.time()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=1500,
                timeout=LLM_TIMEOUT_SECONDS,
            )
            latency_ms = int((time.time() - start_time) * 1000)

            content = response.choices[0].message.content or ""
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0

            # Cost estimation (EC-3.9)
            costs = COST_PER_1K_TOKENS.get(self.model, {"input": 0, "output": 0})
            estimated_cost = (
                (input_tokens / 1000) * costs["input"]
                + (output_tokens / 1000) * costs["output"]
            )

            logger.info(
                f"OpenAI response: {input_tokens} in / {output_tokens} out tokens, "
                f"{latency_ms}ms, ~${estimated_cost:.4f}"
            )

            return LLMResponse(
                content=content,
                provider=self.provider_name,
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                estimated_cost_usd=estimated_cost,
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"OpenAI error: {error_msg}")

            # Detect rate limiting (EC-3.5)
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                error_msg = "Rate limit exceeded. Please try again in a moment."

            return LLMResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                success=False,
                error=error_msg,
            )


# ---------------------------------------------------------------------------
# Google Gemini Provider
# ---------------------------------------------------------------------------

class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider."""

    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.model = GEMINI_MODEL
        self.provider_name = "gemini"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key != "your-gemini-api-key-here")

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                self.model,
                system_instruction=system_prompt,
            )

            start_time = time.time()
            response = model.generate_content(
                user_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1500,
                ),
            )
            latency_ms = int((time.time() - start_time) * 1000)

            content = response.text or ""

            # Gemini doesn't always expose token counts
            input_tokens = 0
            output_tokens = 0
            try:
                if hasattr(response, "usage_metadata"):
                    input_tokens = getattr(response.usage_metadata, "prompt_token_count", 0)
                    output_tokens = getattr(response.usage_metadata, "candidates_token_count", 0)
            except Exception:
                pass

            logger.info(
                f"Gemini response: ~{input_tokens} in / ~{output_tokens} out tokens, "
                f"{latency_ms}ms"
            )

            return LLMResponse(
                content=content,
                provider=self.provider_name,
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                estimated_cost_usd=0.0,
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Gemini error: {error_msg}")
            return LLMResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                success=False,
                error=error_msg,
            )


# ---------------------------------------------------------------------------
# Groq Provider
# ---------------------------------------------------------------------------

class GroqProvider(BaseLLMProvider):
    """Groq LLM provider."""

    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.model = GROQ_MODEL
        self.provider_name = "groq"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key != "your-groq-api-key-here")

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        try:
            from groq import Groq

            client = Groq(api_key=self.api_key)

            start_time = time.time()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=1500,
                timeout=LLM_TIMEOUT_SECONDS,
            )
            latency_ms = int((time.time() - start_time) * 1000)

            content = response.choices[0].message.content or ""
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0

            # Cost estimation
            costs = COST_PER_1K_TOKENS.get(self.model, {"input": 0, "output": 0})
            estimated_cost = (
                (input_tokens / 1000) * costs["input"]
                + (output_tokens / 1000) * costs["output"]
            )

            logger.info(
                f"Groq response: {input_tokens} in / {output_tokens} out tokens, "
                f"{latency_ms}ms, ~${estimated_cost:.4f}"
            )

            return LLMResponse(
                content=content,
                provider=self.provider_name,
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                estimated_cost_usd=estimated_cost,
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Groq error: {error_msg}")

            # Detect rate limiting
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                error_msg = "Rate limit exceeded. Please try again in a moment."

            return LLMResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                success=False,
                error=error_msg,
            )


# ---------------------------------------------------------------------------
# Ollama Provider (Local)
# ---------------------------------------------------------------------------

class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider."""

    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL
        self.provider_name = "ollama"

    def is_available(self) -> bool:
        try:
            import requests
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        try:
            import requests

            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.7},
                },
                timeout=LLM_TIMEOUT_SECONDS,
            )
            latency_ms = int((time.time() - start_time) * 1000)

            data = response.json()
            content = data.get("message", {}).get("content", "")

            input_tokens = data.get("prompt_eval_count", 0)
            output_tokens = data.get("eval_count", 0)

            logger.info(
                f"Ollama response: {input_tokens} in / {output_tokens} out tokens, "
                f"{latency_ms}ms"
            )

            return LLMResponse(
                content=content,
                provider=self.provider_name,
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                estimated_cost_usd=0.0,
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Ollama error: {error_msg}")
            return LLMResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                success=False,
                error=error_msg,
            )


# ---------------------------------------------------------------------------
# Provider Registry & Auto-Selection (EC-3.7)
# ---------------------------------------------------------------------------

# Priority order for failover
PROVIDER_PRIORITY = ["groq", "openai", "gemini", "ollama"]

PROVIDERS = {
    "groq": GroqProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
}


def get_provider(preferred: str = "") -> BaseLLMProvider | None:
    """
    Get the best available LLM provider.

    Tries the preferred provider first, then falls back through
    the priority list (EC-3.7).

    Args:
        preferred: Preferred provider name (from config)

    Returns:
        An initialized LLM provider, or None if none available
    """
    preferred = preferred or LLM_PROVIDER

    # Try preferred provider first
    if preferred in PROVIDERS:
        provider = PROVIDERS[preferred]()
        if provider.is_available():
            logger.info(f"Using preferred LLM provider: {preferred}")
            return provider
        logger.warning(f"Preferred provider '{preferred}' is not available.")

    # Failover to other providers
    for name in PROVIDER_PRIORITY:
        if name == preferred:
            continue
        provider = PROVIDERS[name]()
        if provider.is_available():
            logger.info(f"Failover to LLM provider: {name}")
            return provider

    logger.error("No LLM provider is available.")
    return None


def generate_completion(system_prompt: str, user_prompt: str) -> LLMResponse:
    """
    Generate an LLM completion using the best available provider.

    Args:
        system_prompt: System/instruction prompt
        user_prompt: User prompt with context and question

    Returns:
        LLMResponse object
    """
    provider = get_provider()

    if provider is None:
        return LLMResponse(
            content="",
            provider="none",
            model="none",
            success=False,
            error=(
                "No LLM provider is available. "
                "Please configure an API key in your .env file."
            ),
        )

    return provider.generate(system_prompt, user_prompt)

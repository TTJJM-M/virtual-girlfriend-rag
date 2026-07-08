from typing import AsyncGenerator, List, Dict, Any, Optional
from openai import AsyncOpenAI
from app.config import model_pool, settings
import time


class LLMService:
    """DashScope LLM service with automatic model failover and streaming"""

    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.base_url = settings.DASHSCOPE_BASE_URL

    def _get_client(self, model: str) -> AsyncOpenAI:
        """Create OpenAI-compatible client for specific model"""
        return AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            default_headers={"X-DashScope-Model": model},
        )

    async def _stream_with_retry(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Stream response with specific model"""
        try:
            client = self._get_client(model)
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            return
        except Exception as e:
            error_str = str(e)
            model_pool.mark_error(model, error_str)
            raise

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[tuple[str, str], None]:
        """
        Stream chat response with automatic model failover.
        Yields: (model_used, content_chunk)
        """
        last_error = None

        # Try models in priority order
        for model in [mq.model for mq in model_pool.llm_models]:
            try:
                async for chunk in self._stream_with_retry(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ):
                    yield (model, chunk)
                return  # Success, exit
            except Exception as e:
                last_error = e
                # Continue to next model
                continue

        # All models failed
        if last_error:
            raise last_error
        raise RuntimeError("All LLM models are exhausted")

    async def chat_complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> tuple[str, str]:
        """
        Non-streaming chat with automatic model failover.
        Returns: (model_used, full_response)
        """
        last_error = None
        chunks = []
        model_used = None

        for model in [mq.model for mq in model_pool.llm_models]:
            try:
                model_used = model
                async for chunk in self._stream_with_retry(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ):
                    chunks.append(chunk)
                return (model_used, "".join(chunks))
            except Exception as e:
                last_error = e
                continue

        if last_error:
            raise last_error
        raise RuntimeError("All LLM models are exhausted")

    def get_model_status(self) -> dict:
        """Get current model pool status"""
        return model_pool.get_status()

    def reset_model(self, model: str):
        """Reset a model's exhausted status"""
        model_pool.reset_model(model)


# Singleton instance
llm_service = LLMService()

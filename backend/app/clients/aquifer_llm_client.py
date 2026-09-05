import os

from openai import AsyncOpenAI


class AquiferLLMClient:
    def __init__(
        self,
        base_url: str | None = None,
        model_name: str | None = None,
        timeout: float = 300,
    ):
        self.model_name = (
            model_name
            or os.getenv("AQUIFER_LLM_MODEL")
            or "Qwen/Qwen3-4B-Instruct-2507"
        )
        self.client = AsyncOpenAI(
            api_key="EMPTY",
            base_url=base_url or os.getenv("VLLM_BASE_URL") or "http://127.0.0.1:8002/v1",
            timeout=timeout,
            max_retries=0,
        )

    async def generate(self, messages: list[dict]) -> str | None:
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content

# Sends API calls to the LLM server and returns the LLM response
import os
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key="EMPTY",
    base_url=os.getenv("VLLM_BASE_URL")
)

async def generate(messages):
    response = await client.chat.completions.create(
        model="Qwen/Qwen3-4B-Instruct-2507",
        messages=messages,
        temperature=0,
        max_tokens=1024,
        response_format={"type": "json_object"},
    )

    return response.choices[0].message.content

# Sends API calls to the LLM server and returns the LLM response
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key="EMPTY",
    base_url="http://localhost:8000/v1"
)

async def generate(messages):
    response = await client.chat.completions.create(
        model="Qwen/Qwen3-4B-Instruct-2507",
        messages=messages,
        temperature=0.2
    )

    return response.choices[0].message.content

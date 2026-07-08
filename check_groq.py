import os
import asyncio
from groq import AsyncGroq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

async def test_groq():
    try:
        client = AsyncGroq(api_key=GROQ_API_KEY)
        completion = await client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": "Oi"}],
            max_tokens=10,
        )
        print(f"Groq OK: {completion.choices[0].message.content}")
    except Exception as e:
        print(f"Groq Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_groq())

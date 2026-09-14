import asyncio
import os
import json
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv('c:/Projects/Pilgrim/.env')

async def main():
    api_key = os.getenv('GROQ_API_KEY')
    model = os.getenv('GROQ_MODEL')
    print(f"Model: {model}")
    print(f"API Key start: {api_key[:5] if api_key else None}")
    
    client = AsyncGroq(api_key=api_key)
    
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Tell me about Yadadri."}],
            temperature=0.1,
            max_tokens=800,
            timeout=15.0
        )
        print("HTTP/API success")
        # Print relevant properties safely
        choice = response.choices[0]
        print(f"response.choices[0].message.content: {repr(choice.message.content)}")
        print(f"response.choices[0].message.reasoning: {repr(getattr(choice.message, 'reasoning', None))}")
        print(f"finish_reason: {choice.finish_reason}")
    except Exception as e:
        print(f"HTTP/API failure: {type(e).__name__} - {str(e)}")

asyncio.run(main())

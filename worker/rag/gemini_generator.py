import asyncio
from rag.config import settings

def build_prompt(query, context):
    return f"""
You are PilgrimAI, an assistant for pilgrims.

Use ONLY the provided context. Do not invent phone numbers, prices, or hours.
If a field is missing in the context, say it is not specified.
Do not copy one hotel's phone onto another hotel.

If the user asks for hostels, lodges, dharmashalas, rooms, or places to stay,
answer using the hotel/accommodation records in the context.
If the user asks for food or tiffin, use restaurant records.
If the user asks for a doctor or clinic, use hospital/emergency records.

If the context has no relevant records, say:
"I don't have enough verified information to answer that."

User Question:
{query}

Retrieved Context:
{context}

Give a clear, concise answer. Use only names and numbers that appear in the context.
"""

async def generate_answer(query: str, context: str, app_state) -> str:
    prompt = build_prompt(query, context)

    if not app_state.groq:
        return (
            "GROQ_API_KEY is missing. Here is the retrieved information:\n\n"
            + context[:1200]
        )

    try:
        response = await app_state.groq.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=800,
            timeout=15.0
        )
        return response.choices[0].message.content
    except asyncio.TimeoutError:
        print("  Groq failed: TimeoutError", flush=True)
        return "The language service timed out. Here is the retrieved information:\n\n" + context[:1200]
    except Exception as error:
        print(f"  Groq failed: {error}", flush=True)
        return "The language service is busy. Here is the retrieved information:\n\n" + context[:1200]
import os

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


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


def generate_with_groq(prompt):
    from groq import Groq

    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=800,
    )
    return response.choices[0].message.content


def generate_answer(query, context):
    prompt = build_prompt(query, context)

    if not GROQ_API_KEY:
        return (
            "GROQ_API_KEY is missing. Here is the retrieved information:\n\n"
            + context[:1200]
        )

    try:
        print(f"  Groq: {GROQ_MODEL}", flush=True)
        return generate_with_groq(prompt)
    except Exception as error:
        print(f"  Groq failed: {error}", flush=True)
        return (
            "The language service is busy. Here is the retrieved information:\n\n"
            + context[:1200]
        )
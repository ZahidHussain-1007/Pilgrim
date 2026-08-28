from test_context import search
from gemini_generator import generate_answer


tests = [
    "What are the darshan timings?",
    "What sevas are available?",
    "Tell me about the history of the temple.",
    "What is the dress code?",
    "How can I reach the temple?",
    "What is the best time to visit?",
    "What are the temple contact details?",
    "What is the architectural style?",
    "What facilities are available?",
    "What are the nearby places?"
]


TEMPLE_ID = "T0001"


for i, query in enumerate(tests, 1):

    print("\n")
    print("=" * 80)
    print(f"TEST {i}")
    print(f"QUERY: {query}")
    print("=" * 80)

    results = search(
        query,
        temple_id=TEMPLE_ID
    )

    if not results:
        print("NO RESULTS")
        continue

    print("\nTOP RETRIEVED SECTIONS:")

    for j, result in enumerate(results, 1):

        payload = result["payload"]

        print(
            f"{j}. "
            f"{payload.get('section')} "
            f"| score={result['score']:.4f}"
        )

    context = "\n\n".join(
        result["payload"].get("text", "")
        for result in results
    )

    answer = generate_answer(
        query=query,
        context=context
    )

    print("\nPILGRIMAI ANSWER:")
    print(answer)
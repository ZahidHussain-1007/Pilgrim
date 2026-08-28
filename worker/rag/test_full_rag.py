from test_reranker import search
from context_builder import build_context
from gemini_generator import generate_answer


query = "What are the darshan timings?"


results = search(
    query,
    temple_id="T0001"
)


context = build_context(
    results,
    max_chunks=5
)


answer = generate_answer(
    query,
    context
)


print("\n")
print("=" * 80)
print("PILGRIMAI ANSWER")
print("=" * 80)

print(answer)
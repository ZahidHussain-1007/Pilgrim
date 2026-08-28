from test_reranker import search
from context_builder import build_context


query = "What are the darshan timings?"

if __name__ == "__main__":
    results = search(
        "What are the darshan timings?",
        temple_id="T0001"
    )

    # rest of your testing code

context = build_context(results)

print("\n")
print("=" * 80)
print("FINAL CONTEXT")
print("=" * 80)
print(context)
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue


MODEL_NAME = "BAAI/bge-m3"
COLLECTION_NAME = "pilgrim_temples"

model = SentenceTransformer(MODEL_NAME)

client = QdrantClient(
    path="qdrant_data"
)


def search(query, temple_id=None, limit=5):

    query_vector = model.encode(
        query,
        normalize_embeddings=True
    ).tolist()

    query_filter = None

    if temple_id:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="temple_id",
                    match=MatchValue(
                        value=temple_id
                    )
                )
            ]
        )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=limit
    ).points

    print("\n" + "=" * 70)
    print(f"QUERY: {query}")
    print(f"TEMPLE FILTER: {temple_id}")
    print("=" * 70)

    if not results:
        print("No results found.")
        return

    for i, result in enumerate(results, 1):

        payload = result.payload

        print(f"\nRESULT {i}")
        print("-" * 50)

        print(f"Score    : {result.score:.4f}")
        print(f"Temple   : {payload.get('temple_id')}")
        print(f"Section  : {payload.get('section')}")
        print(f"Chunk ID  : {payload.get('chunk_id')}")
        print(f"Doc ID   : {payload.get('doc_id')}")

        print("\nText:")
        print(payload.get("text", ""))


if __name__ == "__main__":

    search(
        "What are the darshan timings?",
        temple_id="T0001",
        limit=5
    )

    search(
        "Tell me about the history of the temple",
        temple_id="T0001",
        limit=5
    )

    search(
        "What sevas are available?",
        temple_id="T0001",
        limit=5
    )
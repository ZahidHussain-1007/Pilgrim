import atexit

from st_safe_import import SentenceTransformer

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue


EMBEDDING_MODEL = "BAAI/bge-m3"
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"

COLLECTION_NAME = "pilgrim_temples"

TOP_K_RETRIEVE = 10
TOP_K_FINAL = 10


print("Loading embedding model...")

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)

client = QdrantClient(
    path="qdrant_data"
)

reranker = None


def get_reranker():
    global reranker
    if reranker is None:
        print("Loading reranker...")
        from FlagEmbedding import FlagReranker
        reranker = FlagReranker(
            RERANKER_MODEL,
            use_fp16=False
        )
    return reranker


def _close_qdrant():
    try:
        client.close()
    except Exception:
        pass


atexit.register(_close_qdrant)


def search(query, temple_id=None, entity_type=None, verbose=True, use_reranker=False):

    query_vector = embedding_model.encode(
        query,
        normalize_embeddings=True
    ).tolist()

    must = []

    if temple_id:
        must.append(
            FieldCondition(
                key="temple_id",
                match=MatchValue(value=temple_id),
            )
        )

    if entity_type:
        must.append(
            FieldCondition(
                key="entity_type",
                match=MatchValue(value=entity_type),
            )
        )

    query_filter = Filter(must=must) if must else None

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=TOP_K_RETRIEVE
    ).points

    if not results:
        if verbose:
            print("No results found.")
        return []

    if not use_reranker:
        final_results = [
            {
                "payload": result.payload,
                "score": float(result.score),
            }
            for result in results[:TOP_K_FINAL]
        ]
    else:
        model = get_reranker()
        pairs = [
            [query, result.payload["text"]]
            for result in results
        ]
        rerank_scores = model.compute_score(pairs, normalize=True)
        if isinstance(rerank_scores, float):
            rerank_scores = [rerank_scores]
        ranked = sorted(
            zip(results, rerank_scores),
            key=lambda x: x[1],
            reverse=True,
        )
        final_results = [
            {
                "payload": result.payload,
                "score": score,
            }
            for result, score in ranked[:TOP_K_FINAL]
        ]

    if verbose:
        print("\n" + "=" * 80)
        print(f"QUERY: {query}")
        print(f"TEMPLE: {temple_id}")
        print(f"ENTITY: {entity_type}")
        print("=" * 80)
        for i, item in enumerate(final_results, 1):
            payload = item["payload"]
            print(f"\nRESULT {i}")
            print("-" * 60)
            print(f"Score   : {item['score']:.4f}")
            print(f"Temple  : {payload.get('temple_id')}")
            print(f"Section : {payload.get('section')}")

    return final_results


if __name__ == "__main__":

    search(
        "What are the darshan timings?",
        temple_id="T0001",
        entity_type="temple",
    )
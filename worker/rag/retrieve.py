import asyncio
from rag.searcher import search

FUSION_QUERY = (
    "temple overview history location darshan timings "
    "facilities dress code"
)

def rrf_fuse(lists, k=60):
    scores = {}
    payloads = {}
    for results in lists:
        for rank, item in enumerate(results, start=1):
            chunk_id = item["payload"].get("chunk_id")
            if not chunk_id:
                continue
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
            payloads[chunk_id] = item["payload"]

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [
        {"payload": payloads[chunk_id], "score": score}
        for chunk_id, score in ranked
    ]

def boost_sections(results, preferred):
    if not preferred or not results:
        return results
    preferred = set(preferred)
    first = [item for item in results if item["payload"].get("section") in preferred]
    rest = [item for item in results if item["payload"].get("section") not in preferred]
    return first + rest

def unique_places(results, entity_type):
    if entity_type not in {"hotel", "restaurant"}:
        return results

    seen = set()
    unique = []
    for item in results:
        payload = item["payload"]
        meta = payload.get("metadata") or {}
        key = (
            payload.get("entity_id")
            or meta.get("hotel_name")
            or meta.get("restaurant_name")
            or payload.get("chunk_id")
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique

async def retrieve(decision, app_state, slot_k=5, overview_k=8, verbose=False, use_reranker=False):
    if not decision.get("should_retrieve"):
        return []

    temple_id = decision["temple_id"]
    entity_type = decision.get("entity") or "temple"

    if decision.get("intent") == "overview":
        query = FUSION_QUERY
        limit = overview_k
    else:
        queries = decision.get("retrieval_queries") or []
        if not queries and decision.get("retrieval_query"):
            queries = [decision["retrieval_query"]]
        if not queries:
            return []
        query = queries[0]
        limit = slot_k

    dense = await search(
        query,
        app_state=app_state,
        temple_id=temple_id,
        entity_type=entity_type,
        verbose=verbose,
        use_reranker=use_reranker,
    )
    
    def _bm25_search():
        return app_state.bm25_store.search(
            query,
            temple_id=temple_id,
            entity_type=entity_type,
            limit=20,
        )
    
    lexical = await asyncio.to_thread(_bm25_search)
    
    def _fuse():
        fused = rrf_fuse([dense, lexical])
        fused = boost_sections(fused, decision.get("preferred_sections") or [])
        fused = unique_places(fused, entity_type)
        return fused[:limit]
        
    return await asyncio.to_thread(_fuse)
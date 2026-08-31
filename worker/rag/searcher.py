import asyncio
from qdrant_client.models import Filter, FieldCondition, MatchValue

COLLECTION_NAME = "pilgrim_temples"
TOP_K_RETRIEVE = 10
TOP_K_FINAL = 10

async def search(query, app_state, temple_id=None, entity_type=None, verbose=True, use_reranker=False):
    def _encode():
        return app_state.embedder.encode(query, normalize_embeddings=True).tolist()
    
    query_vector = await asyncio.to_thread(_encode)

    must = []
    if temple_id:
        must.append(FieldCondition(key="temple_id", match=MatchValue(value=temple_id)))
    if entity_type:
        must.append(FieldCondition(key="entity_type", match=MatchValue(value=entity_type)))

    query_filter = Filter(must=must) if must else None

    # We use asyncio.to_thread for Qdrant client since it's synchronous local path
    def _query_qdrant():
        return app_state.qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=query_filter,
            limit=TOP_K_RETRIEVE
        ).points
        
    results = await asyncio.to_thread(_query_qdrant)

    if not results:
        if verbose:
            print("No results found.")
        return []

    if not use_reranker or not app_state.reranker:
        final_results = [
            {
                "payload": result.payload,
                "score": float(result.score),
            }
            for result in results[:TOP_K_FINAL]
        ]
    else:
        pairs = [[query, result.payload["text"]] for result in results]
        
        def _rerank():
            return app_state.reranker.compute_score(pairs, normalize=True)
            
        rerank_scores = await asyncio.to_thread(_rerank)
        
        if isinstance(rerank_scores, float):
            rerank_scores = [rerank_scores]
            
        ranked = sorted(zip(results, rerank_scores), key=lambda x: x[1], reverse=True)
        final_results = [
            {
                "payload": result.payload,
                "score": float(score),
            }
            for result, score in ranked[:TOP_K_FINAL]
        ]

    return final_results

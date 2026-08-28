def build_context(results, max_chunks=5):

    context_parts = []

    for i, item in enumerate(results[:max_chunks], 1):

        payload = item["payload"]

        context_parts.append(
            f"""SOURCE {i}
Temple ID: {payload.get("temple_id")}
Section: {payload.get("section")}
Chunk ID: {payload.get("chunk_id")}

{payload.get("text", "")}"""
        )

    return "\n\n".join(context_parts)
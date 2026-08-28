import json
from pathlib import Path

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct


CHUNKS_FILE = Path("processed/hotel_chunks.jsonl")
EMBEDDINGS_FILE = Path("processed/hotel_embeddings.npz")
COLLECTION_NAME = "pilgrim_temples"
BATCH_SIZE = 100


def main():
    client = QdrantClient(path="qdrant_data")

    info = client.get_collection(COLLECTION_NAME)
    start_id = info.points_count
    print(f"Existing points : {start_id}")

    data = np.load(EMBEDDINGS_FILE)
    embeddings = data["embeddings"]
    embedding_chunk_ids = data["chunk_ids"]

    chunks = []
    with open(CHUNKS_FILE, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))

    chunk_map = {chunk["chunk_id"]: chunk for chunk in chunks}

    points = []
    for index, chunk_id in enumerate(embedding_chunk_ids):
        chunk_id = str(chunk_id)
        chunk = chunk_map.get(chunk_id)
        if chunk is None:
            raise ValueError(f"Missing chunk: {chunk_id}")

        points.append(
            PointStruct(
                id=start_id + index,
                vector=embeddings[index].tolist(),
                payload={
                    "chunk_id": chunk["chunk_id"],
                    "doc_id": chunk["doc_id"],
                    "temple_id": chunk["temple_id"],
                    "entity_type": chunk["entity_type"],
                    "entity_id": chunk["entity_id"],
                    "section": chunk["section"],
                    "chunk_index": chunk["chunk_index"],
                    "text": chunk["text"],
                    "metadata": chunk["metadata"],
                },
            )
        )

    for start in range(0, len(points), BATCH_SIZE):
        batch = points[start:start + BATCH_SIZE]
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=batch,
        )
        print(f"Uploaded {min(start + BATCH_SIZE, len(points))}/{len(points)}")

    info = client.get_collection(COLLECTION_NAME)
    print("Hotel Qdrant load complete.")
    print(f"Points stored: {info.points_count}")
    client.close()


if __name__ == "__main__":
    main()
    
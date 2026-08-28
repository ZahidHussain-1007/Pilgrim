import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


INPUT_FILE = Path("processed/temple_chunks.jsonl")
OUTPUT_FILE = Path("processed/temple_embeddings.npz")

MODEL_NAME = "BAAI/bge-m3"

BATCH_SIZE = 16


def main():

    print("Loading embedding model...")

    model = SentenceTransformer(
        MODEL_NAME
    )

    chunks = []

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            if line.strip():
                chunks.append(
                    json.loads(line)
                )

    print(f"Chunks loaded: {len(chunks)}")

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    print("Generating embeddings...")

    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    print(
        f"Embedding shape: {embeddings.shape}"
    )

    chunk_ids = np.array(
        [
            chunk["chunk_id"]
            for chunk in chunks
        ],
        dtype=str
    )

    np.savez_compressed(
        OUTPUT_FILE,
        embeddings=embeddings,
        chunk_ids=chunk_ids
    )

    print("\nEmbedding generation complete.")
    print(f"Chunks       : {len(chunks)}")
    print(f"Dimensions   : {embeddings.shape[1]}")
    print(f"Output       : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()  
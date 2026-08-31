import json
from pathlib import Path

from rank_bm25 import BM25Okapi


ROOT = Path(__file__).resolve().parent.parent
CHUNK_FILES = [
    ROOT / "processed" / "temple_chunks.jsonl",
    ROOT / "processed" / "hotel_chunks.jsonl",
    ROOT / "processed" / "restaurant_chunks.jsonl",
    ROOT / "processed" / "emergency_chunks.jsonl",
]


def tokenize(text):
    return (text or "").lower().split()


class BM25Store:
    def __init__(self):
        self.docs = []
        for path in CHUNK_FILES:
            if not path.exists():
                continue
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        self.docs.append(json.loads(line))

        print(f"BM25 docs loaded: {len(self.docs)}", flush=True)

    def search(self, query, temple_id, entity_type, limit=20):
        subset = [
            doc
            for doc in self.docs
            if doc.get("temple_id") == temple_id
            and doc.get("entity_type") == entity_type
        ]
        if not subset:
            return []

        corpus = [tokenize(doc.get("text", "")) for doc in subset]
        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(tokenize(query))
        ranked = sorted(
            zip(subset, scores),
            key=lambda x: x[1],
            reverse=True,
        )[:limit]

        results = []
        for doc, score in ranked:
            if score <= 0:
                continue
            results.append(
                {
                    "payload": {
                        "chunk_id": doc.get("chunk_id"),
                        "doc_id": doc.get("doc_id"),
                        "temple_id": doc.get("temple_id"),
                        "entity_type": doc.get("entity_type"),
                        "entity_id": doc.get("entity_id"),
                        "section": doc.get("section"),
                        "chunk_index": doc.get("chunk_index"),
                        "text": doc.get("text"),
                        "metadata": doc.get("metadata") or {},
                    },
                    "score": float(score),
                }
            )
        return results
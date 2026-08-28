import json
from pathlib import Path

from transformers import AutoTokenizer


INPUT_FILE = Path("processed/hotel_documents.jsonl")
OUTPUT_FILE = Path("processed/hotel_chunks.jsonl")

MODEL_NAME = "BAAI/bge-m3"

MAX_TOKENS = 700
TARGET_TOKENS = 550
OVERLAP_TOKENS = 80


tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


def token_count(text):
    return len(
        tokenizer.encode(
            text,
            add_special_tokens=False
        )
    )


def split_text(text):
    paragraphs = [
        p.strip()
        for p in text.split("\n")
        if p.strip()
    ]

    if len(paragraphs) > 1:
        chunks = []
        current = []
        current_tokens = 0

        for paragraph in paragraphs:
            p_tokens = token_count(paragraph)

            if current and current_tokens + p_tokens > TARGET_TOKENS:
                chunks.append("\n".join(current))

                overlap = []
                overlap_tokens = 0

                for previous in reversed(current):
                    previous_tokens = token_count(previous)

                    if overlap_tokens + previous_tokens > OVERLAP_TOKENS:
                        break

                    overlap.insert(0, previous)
                    overlap_tokens += previous_tokens

                current = overlap
                current_tokens = overlap_tokens

            current.append(paragraph)
            current_tokens += p_tokens

        if current:
            chunks.append("\n".join(current))

        return chunks

    tokens = tokenizer.encode(
        text,
        add_special_tokens=False
    )

    chunks = []
    step = TARGET_TOKENS - OVERLAP_TOKENS
    start = 0

    while start < len(tokens):
        end = min(start + TARGET_TOKENS, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(
            chunk_tokens,
            skip_special_tokens=True
        )
        chunks.append(chunk_text)

        if end == len(tokens):
            break

        start += step

    return chunks


def create_chunks(document):
    text = document["text"]
    if token_count(text) <= MAX_TOKENS:
        return [text]
    return split_text(text)


def main():
    documents = []
    with open(INPUT_FILE, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                documents.append(json.loads(line))

    total_chunks = 0
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for document in documents:
            chunks = create_chunks(document)
            for index, chunk in enumerate(chunks):
                chunk_document = {
                    "chunk_id": f"{document['doc_id']}_{index + 1:03d}",
                    "doc_id": document["doc_id"],
                    "temple_id": document["temple_id"],
                    "entity_type": document["entity_type"],
                    "entity_id": document["entity_id"],
                    "section": document["section"],
                    "chunk_index": index,
                    "text": chunk,
                    "metadata": document["metadata"],
                }
                out.write(json.dumps(chunk_document, ensure_ascii=False) + "\n")
                total_chunks += 1

    print("Hotel chunking complete.")
    print(f"Documents : {len(documents)}")
    print(f"Chunks    : {total_chunks}")
    print(f"Output    : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
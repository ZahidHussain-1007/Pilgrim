import json
from pathlib import Path
from collections import Counter

from transformers import AutoTokenizer


INPUT_FILE = Path("processed/temple_chunks.jsonl")

MODEL_NAME = "BAAI/bge-m3"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


def count_tokens(text):
    return len(
        tokenizer.encode(
            text,
            add_special_tokens=False
        )
    )


def percentile(values, p):
    values = sorted(values)

    index = int((len(values) - 1) * p)

    return values[index]


def main():

    chunks = []

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            if line.strip():
                chunks.append(json.loads(line))

    print("\n===== CHUNK QUALITY REPORT =====\n")

    print(f"Total chunks: {len(chunks)}")

    token_lengths = []

    empty_chunks = []
    very_short_chunks = []
    oversized_chunks = []

    doc_ids = []
    chunk_ids = []

    temple_counter = Counter()
    section_counter = Counter()

    duplicate_texts = Counter()

    for chunk in chunks:

        text = chunk.get("text", "").strip()

        tokens = count_tokens(text)

        token_lengths.append(tokens)

        doc_ids.append(chunk.get("doc_id"))
        chunk_ids.append(chunk.get("chunk_id"))

        temple_counter[
            chunk.get("temple_id")
        ] += 1

        section_counter[
            chunk.get("section")
        ] += 1

        if not text:
            empty_chunks.append(
                chunk.get("chunk_id")
            )

        if tokens < 20:
            very_short_chunks.append({
                "chunk_id": chunk.get("chunk_id"),
                "tokens": tokens,
                "section": chunk.get("section")
            })

        if tokens > 700:
            oversized_chunks.append({
            "chunk_id": chunk.get("chunk_id"),
            "tokens": tokens,
            "section": chunk.get("section"),
            "doc_id": chunk.get("doc_id"),
            "temple_id": chunk.get("temple_id")
        })

        duplicate_texts[text] += 1

    duplicate_chunks = {
        text: count
        for text, count in duplicate_texts.items()
        if text and count > 1
    }

    duplicate_doc_ids = [
        doc_id
        for doc_id, count in Counter(doc_ids).items()
        if count > 1
    ]

    duplicate_chunk_ids = [
        chunk_id
        for chunk_id, count in Counter(chunk_ids).items()
        if count > 1
    ]

    print("\n===== TOKEN DISTRIBUTION =====\n")

    print(f"Minimum : {min(token_lengths)}")
    print(f"Maximum : {max(token_lengths)}")
    print(f"Average : {sum(token_lengths) / len(token_lengths):.2f}")
    print(f"Median  : {percentile(token_lengths, 0.50)}")
    print(f"P75     : {percentile(token_lengths, 0.75)}")
    print(f"P90     : {percentile(token_lengths, 0.90)}")
    print(f"P95     : {percentile(token_lengths, 0.95)}")
    print(f"P99     : {percentile(token_lengths, 0.99)}")

    print("\n===== QUALITY CHECKS =====\n")

    print(f"Empty chunks          : {len(empty_chunks)}")
    print(f"Very short (<20)      : {len(very_short_chunks)}")
    print(f"Oversized (>700)      : {len(oversized_chunks)}")
    print(f"Duplicate chunk IDs   : {len(duplicate_chunk_ids)}")
    print(f"Duplicate document IDs: {len(duplicate_doc_ids)}")
    print(f"Duplicate texts       : {len(duplicate_chunks)}")

    print("\n===== OVERSIZED CHUNKS =====\n")

    for item in sorted(
        oversized_chunks,
        key=lambda x: x["tokens"],
        reverse=True
    )[:20]:

        print(
            f"{item['tokens']:5} tokens | "
            f"{item['temple_id'] if 'temple_id' in item else ''} | "
            f"{item['section']} | "
            f"{item['chunk_id']}"
        )

    print("\n===== VERY SHORT CHUNKS =====\n")

    for item in very_short_chunks[:20]:

        print(
            f"{item['tokens']:3} tokens | "
            f"{item['section']} | "
            f"{item['chunk_id']}"
        )

    print("\n===== CHUNKS PER TEMPLE =====\n")

    for temple_id, count in sorted(
        temple_counter.items()
    ):
        print(
            f"{temple_id}: {count}"
        )

    print("\n===== CHUNKS PER SECTION =====\n")

    for section, count in sorted(
        section_counter.items(),
        key=lambda x: x[1],
        reverse=True
    ):
        print(
            f"{section}: {count}"
        )

    print("\n===== VALIDATION =====\n")

    checks = {
        "No empty chunks": len(empty_chunks) == 0,
        "No duplicate chunk IDs": len(duplicate_chunk_ids) == 0,
        "No duplicate document IDs": len(duplicate_doc_ids) == 0,
    }

    for name, passed in checks.items():

        print(
            f"{'PASS' if passed else 'FAIL'} - {name}"
        )

    print("\nValidation complete.")


if __name__ == "__main__":
    main()
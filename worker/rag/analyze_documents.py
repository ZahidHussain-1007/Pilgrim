import json
from pathlib import Path
from transformers import AutoTokenizer


INPUT_FILE = Path("processed/temple_documents.jsonl")

MODEL_NAME = "BAAI/bge-m3"


def main():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    lengths = []
    documents = []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            doc = json.loads(line)

            text = doc["text"]
            tokens = tokenizer.encode(
                text,
                add_special_tokens=False
            )

            token_count = len(tokens)

            lengths.append(token_count)
            documents.append({
                "doc_id": doc["doc_id"],
                "temple_id": doc["temple_id"],
                "section": doc["section"],
                "tokens": token_count
            })

    lengths.sort()

    if not lengths:
        print("No documents found.")
        return

    n = len(lengths)

    def percentile(p):
        index = int((n - 1) * p)
        return lengths[index]

    print("\n===== DOCUMENT TOKEN ANALYSIS =====\n")

    print(f"Documents       : {n}")
    print(f"Minimum tokens  : {min(lengths)}")
    print(f"Maximum tokens  : {max(lengths)}")
    print(f"Average tokens  : {sum(lengths) / n:.2f}")
    print(f"Median tokens   : {percentile(0.50)}")
    print(f"75th percentile : {percentile(0.75)}")
    print(f"90th percentile : {percentile(0.90)}")
    print(f"95th percentile : {percentile(0.95)}")
    print(f"99th percentile : {percentile(0.99)}")

    print("\n===== LARGEST DOCUMENTS =====\n")

    largest = sorted(
        documents,
        key=lambda x: x["tokens"],
        reverse=True
    )[:20]

    for doc in largest:
        print(
            f"{doc['tokens']:5} tokens | "
            f"{doc['temple_id']} | "
            f"{doc['section']} | "
            f"{doc['doc_id']}"
        )


if __name__ == "__main__":
    main()
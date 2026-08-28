import json
from pathlib import Path


INPUT_DIR = Path("data/temples")
OUTPUT_DIR = Path("processed")
OUTPUT_FILE = OUTPUT_DIR / "temple_documents.jsonl"


def clean_text(value):
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, list):
        parts = []
        for item in value:
            text = clean_text(item)
            if text:
                parts.append(text)
        return " ".join(parts)

    if isinstance(value, dict):
        parts = []
        for key, val in value.items():
            text = clean_text(val)
            if text:
                parts.append(f"{key.replace('_', ' ')}: {text}")
        return " ".join(parts)

    return str(value)


def get_text(value):
    if isinstance(value, str):
        return value.strip()

    if isinstance(value, dict):
        if "en" in value and value["en"]:
            return value["en"].strip()

        return clean_text(value)

    return clean_text(value)


def create_document(
    temple_id,
    temple_name,
    section,
    text,
    source_file,
    location,
    base_metadata
):
    text = text.strip()

    if not text:
        return None

    return {
        "doc_id": f"{temple_id}_{section}",
        "temple_id": temple_id,
        "entity_type": "temple",
        "entity_id": temple_id,
        "section": section,
        "text": text,
        "metadata": {
            "temple_name": temple_name,
            "source_file": source_file,
            "source_type": "canonical_temple_record",
            "district": location.get("district", ""),
            "state": location.get("state", ""),
            "country": location.get("country", ""),
            **base_metadata
        }
    }


def normalize_temple(data, source_file):
    temple_id = data.get("temple_id")

    if not temple_id:
        raise ValueError(f"Missing temple_id in {source_file}")

    temple_name = (
        data.get("name")
        or data.get("temple_name")
        or data.get("templeName")
        or temple_id
    )

    location = data.get("location", {})

    base_metadata = {
        "religion": data.get("religion", ""),
        "category": data.get("category", ""),
        "temple_type": data.get("temple_type", ""),
        "pincode": location.get("pincode", ""),
        "latitude": location.get("latitude"),
        "longitude": location.get("longitude"),
        "timezone": location.get("timezone", "")
    }

    documents = []

    # Identity / overview
    overview_parts = []

    if data.get("alternate_names"):
        overview_parts.append(
            "Alternate names: " +
            clean_text(data["alternate_names"])
        )

    multilingual = data.get("multilingual", {})

    if multilingual.get("alternate_spellings"):
        overview_parts.append(
            "Alternate spellings: " +
            clean_text(multilingual["alternate_spellings"])
        )

    if data.get("deity"):
        deity = data["deity"]

        if isinstance(deity, dict):
            presiding = deity.get("presiding_deity")
            others = deity.get("other_deities")

            if presiding:
                overview_parts.append(
                    f"Presiding deity: {clean_text(presiding)}"
                )

            if others:
                overview_parts.append(
                    f"Other deities: {clean_text(others)}"
                )
        else:
            overview_parts.append(
                f"Deity: {clean_text(deity)}"
            )

    if data.get("overview"):
        overview_parts.append(
            get_text(data["overview"])
        )

    if overview_parts:
        documents.append(
            create_document(
                temple_id,
                temple_name,
                "overview",
                " ".join(overview_parts),
                source_file,
                location,
                base_metadata
            )
        )

    # Simple semantic sections
    sections = [
        "history",
        "sthala_puranam",
        "religious_significance",
        "spiritual_significance",
        "architecture",
        "architectural_style",
        "dress_code",
        "best_time_to_visit",
        "travel_guide",
        "travel",
        "accessibility",
        "contact"
    ]

    for section in sections:
        if section not in data:
            continue

        text = get_text(data[section])

        document = create_document(
            temple_id,
            temple_name,
            section,
            text,
            source_file,
            location,
            base_metadata
        )

        if document:
            documents.append(document)

    # List-based sections
    list_sections = [
        "healing_beliefs",
        "miracles_and_devotee_experiences",
        "temple_layout",
        "rituals",
        "special_poojas",
        "facilities"
    ]

    for section in list_sections:
        if section not in data:
            continue

        text = get_text(data[section])

        document = create_document(
            temple_id,
            temple_name,
            section,
            text,
            source_file,
            location,
            base_metadata
        )

        if document:
            documents.append(document)

    # Nested structured sections
    nested_sections = [
        "darshan_timings",
        "sevas",
        "darshan_and_tickets",
        "accommodation",
        "nearby_places",
        "nearby_infrastructure"
    ]

    for section in nested_sections:
        if section not in data:
            continue

        text = clean_text(data[section])

        document = create_document(
            temple_id,
            temple_name,
            section,
            text,
            source_file,
            location,
            base_metadata
        )

        if document:
            documents.append(document)

    # FAQ: one FAQ = one document
    for faq in data.get("faq", []):
        question = clean_text(faq.get("question"))
        answer = clean_text(faq.get("answer"))
        faq_id = faq.get("id", "unknown")

        if not question or not answer:
            continue

        text = f"Question: {question}\nAnswer: {answer}"

        document = create_document(
            temple_id,
            temple_name,
            f"faq_{faq_id}",
            text,
            source_file,
            location,
            {
                **base_metadata,
                "faq_id": faq_id
            }
        )

        if document:
            document["doc_id"] = f"{temple_id}_faq_{faq_id}"
            documents.append(document)

    return documents


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_documents = []
    seen_ids = set()

    files = sorted(INPUT_DIR.glob("*.json"))

    if not files:
        raise FileNotFoundError(
            f"No JSON files found in {INPUT_DIR}"
        )

    for file_path in files:
        print(f"Processing: {file_path.name}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        documents = normalize_temple(
            data,
            file_path.name
        )

        for document in documents:
            if document["doc_id"] in seen_ids:
                raise ValueError(
                    f"Duplicate doc_id: {document['doc_id']}"
                )

            if not document["text"]:
                continue

            seen_ids.add(document["doc_id"])
            all_documents.append(document)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        for document in all_documents:
            f.write(
                json.dumps(
                    document,
                    ensure_ascii=False
                ) + "\n"
            )

    print("\nNormalization complete.")
    print(f"Temple files: {len(files)}")
    print(f"RAG documents: {len(all_documents)}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
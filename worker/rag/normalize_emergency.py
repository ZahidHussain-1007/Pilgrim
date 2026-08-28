import json
from pathlib import Path


INPUT_DIR = Path("data/emergency")
OUTPUT_DIR = Path("processed")
OUTPUT_FILE = OUTPUT_DIR / "emergency_documents.jsonl"


SECTIONS = [
    ("hospitals", "hospital", "name"),
    ("ambulance_services", "ambulance", "service_name"),
    ("police", "police", "police_station_name"),
    ("fire_rescue", "fire", "fire_station_name"),
    ("pharmacies", "pharmacy", "name"),
]


def clean_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return " ".join(t for t in (clean_text(item) for item in value) if t)
    if isinstance(value, dict):
        parts = []
        for key, val in value.items():
            text = clean_text(val)
            if text:
                parts.append(f"{key.replace('_', ' ')}: {text}")
        return " ".join(parts)
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def item_name(item, name_key):
    return clean_text(
        item.get(name_key)
        or item.get("name")
        or item.get("service_name")
        or ""
    )


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(INPUT_DIR.rglob("*.json"))
    if not files:
        raise FileNotFoundError(f"No emergency JSON files in {INPUT_DIR}")

    documents = []
    by_temple = {}

    for path in files:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        temple_id = data.get("temple_id") or data.get("templeId")
        temple_name = data.get("temple_name") or data.get("templeName") or ""
        if not temple_id:
            raise ValueError(f"Missing temple_id in {path}")

        block = data.get("emergency") or {}
        location = clean_text(data.get("location"))

        for source_key, section, name_key in SECTIONS:
            items = block.get(source_key) or []
            usable = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                if not item_name(item, name_key) and not clean_text(item.get("phone") or item.get("address")):
                    continue
                usable.append(item)

            if not usable:
                continue

            parts = [
                f"Emergency {section} information for {temple_name or temple_id}."
            ]
            if location:
                parts.append(f"Temple location: {location}")

            for item in usable:
                name = item_name(item, name_key) or section
                parts.append(f"{section.title()}: {name}")
                parts.append(clean_text(item))

            text = "\n".join(parts)
            doc_id = f"{temple_id}_emergency_{section}"
            by_temple[temple_id] = by_temple.get(temple_id, 0) + 1

            documents.append(
                {
                    "doc_id": doc_id,
                    "temple_id": temple_id,
                    "entity_type": "emergency",
                    "entity_id": doc_id,
                    "section": section,
                    "text": text,
                    "metadata": {
                        "temple_name": temple_name,
                        "source_file": str(path.as_posix()),
                        "source_type": "emergency_record",
                    },
                }
            )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for document in documents:
            f.write(json.dumps(document, ensure_ascii=False) + "\n")

    print("Emergency normalization complete.")
    print(f"Files     : {len(files)}")
    print(f"Documents : {len(documents)}")
    print(f"Output    : {OUTPUT_FILE}")
    print("Per temple:")
    for temple_id, count in sorted(by_temple.items()):
        print(f"  {temple_id}: {count}")


if __name__ == "__main__":
    main()
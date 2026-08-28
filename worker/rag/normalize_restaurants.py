import json
from pathlib import Path


INPUT_DIR = Path("data/restaurants")
OUTPUT_DIR = Path("processed")
OUTPUT_FILE = OUTPUT_DIR / "restaurant_documents.jsonl"


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


def unique_doc_id(base, seen):
    if base not in seen:
        return base, False
    index = 2
    while f"{base}_{index}" in seen:
        index += 1
    return f"{base}_{index}", True


def restaurant_text(data, temple_name):
    parts = []
    name = clean_text(data.get("restaurantName") or data.get("restaurant_name"))
    if name:
        parts.append(f"Restaurant name: {name}")
    if temple_name:
        parts.append(f"Near temple: {temple_name}")

    basic = data.get("basicInformation") or {}
    if basic.get("category"):
        parts.append(f"Category: {clean_text(basic.get('category'))}")
    if basic.get("cuisineType"):
        parts.append(f"Cuisine: {clean_text(basic.get('cuisineType'))}")
    if basic.get("shortDescription"):
        parts.append(clean_text(basic.get("shortDescription")))

    loc = data.get("location") or {}
    address = clean_text(loc.get("fullAddress") or loc.get("address"))
    if address:
        parts.append(f"Address: {address}")
    if loc.get("landmark"):
        parts.append(f"Landmark: {clean_text(loc.get('landmark'))}")

    travel = data.get("travelInformation") or {}
    if travel:
        parts.append("Travel: " + clean_text(travel))

    contact = data.get("contactInformation") or {}
    if contact.get("phoneNumber"):
        parts.append(f"Phone: {clean_text(contact.get('phoneNumber'))}")

    hours = data.get("workingHours") or {}
    if hours:
        parts.append("Hours: " + clean_text(hours))

    food = data.get("foodInformation") or {}
    if food:
        parts.append("Menu: " + clean_text(food))

    price = data.get("priceInformation") or {}
    if price:
        parts.append("Price: " + clean_text(price))

    facilities = data.get("facilities") or {}
    if facilities:
        parts.append("Facilities: " + clean_text(facilities))

    diet = data.get("dietaryInformation") or {}
    if diet:
        parts.append("Dietary: " + clean_text(diet))

    reviews = data.get("customerInformation") or {}
    if reviews:
        parts.append("Reviews: " + clean_text(reviews))

    highlights = data.get("restaurantHighlights") or []
    if highlights:
        parts.append("Highlights: " + clean_text(highlights))

    maps = clean_text(data.get("googleMapsLink") or loc.get("googleMapsLink"))
    if maps:
        parts.append(f"Maps: {maps}")

    return "\n".join(parts)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(INPUT_DIR.rglob("*.json"))
    if not files:
        raise FileNotFoundError(f"No restaurant JSON files in {INPUT_DIR}")

    documents = []
    seen = set()
    by_temple = {}
    duplicates = []

    for path in files:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        assoc = data.get("associatedTemple") or data.get("associated_temple") or {}
        if isinstance(assoc, str):
            temple_name = assoc
            temple_id = data.get("temple_id") or data.get("templeId")
        else:
            temple_name = assoc.get("templeName") or assoc.get("temple_name") or ""
            temple_id = (
                assoc.get("templeId")
                or assoc.get("temple_id")
                or data.get("temple_id")
                or data.get("templeId")
            )

        restaurant_id = (
            data.get("restaurantId")
            or data.get("restaurant_id")
            or path.stem
        )
        name = data.get("restaurantName") or data.get("restaurant_name") or restaurant_id

        if not temple_id:
            raise ValueError(f"Missing temple_id in {path}")

        text = restaurant_text(data, temple_name)
        if not text.strip():
            continue

        doc_id, was_duplicate = unique_doc_id(f"{temple_id}_{restaurant_id}", seen)
        if was_duplicate:
            duplicates.append(f"{path.name} -> {doc_id}")
        seen.add(doc_id)
        by_temple[temple_id] = by_temple.get(temple_id, 0) + 1

        documents.append(
            {
                "doc_id": doc_id,
                "temple_id": temple_id,
                "entity_type": "restaurant",
                "entity_id": restaurant_id,
                "section": "restaurant",
                "text": text,
                "metadata": {
                    "restaurant_name": name,
                    "associated_temple": temple_name,
                    "source_file": str(path.as_posix()),
                    "source_type": "restaurant_record",
                },
            }
        )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for document in documents:
            f.write(json.dumps(document, ensure_ascii=False) + "\n")

    print("Restaurant normalization complete.")
    print(f"Files      : {len(files)}")
    print(f"Documents  : {len(documents)}")
    print(f"Duplicates : {len(duplicates)}")
    for item in duplicates:
        print(f"  {item}")
    print(f"Output     : {OUTPUT_FILE}")
    print("Per temple:")
    for temple_id, count in sorted(by_temple.items()):
        print(f"  {temple_id}: {count}")


if __name__ == "__main__":
    main()
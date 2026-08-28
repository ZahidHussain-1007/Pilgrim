import json
from pathlib import Path


INPUT_DIR = Path("data/accommodations")
OUTPUT_DIR = Path("processed")
OUTPUT_FILE = OUTPUT_DIR / "hotel_documents.jsonl"


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


def hotel_text(hotel, associated_temple):
    parts = []

    name = clean_text(hotel.get("hotel_name"))
    if name:
        parts.append(f"Hotel name: {name}")

    if associated_temple:
        parts.append(f"Near temple: {associated_temple}")

    fields = [
        ("hotel_type", "Type"),
        ("address", "Address"),
        ("about", "About"),
        ("price_range", "Price range"),
        ("check_in_time", "Check in"),
        ("check_out_time", "Check out"),
        ("cancellation_policy", "Cancellation"),
    ]
    for key, label in fields:
        text = clean_text(hotel.get(key))
        if text:
            parts.append(f"{label}: {text}")

    phones = clean_text(hotel.get("contact_numbers"))
    if phones:
        parts.append(f"Phone: {phones}")

    email = clean_text(hotel.get("email"))
    if email:
        parts.append(f"Email: {email}")

    website = clean_text(hotel.get("official_website"))
    if website:
        parts.append(f"Website: {website}")

    maps = clean_text(hotel.get("google_map_link"))
    if maps:
        parts.append(f"Maps: {maps}")

    transport = hotel.get("nearest_transport")
    if transport:
        parts.append("Nearest transport: " + clean_text(transport))

    rooms = clean_text(hotel.get("room_types"))
    if rooms:
        parts.append(f"Room types: {rooms}")

    amenities = clean_text(hotel.get("amenities"))
    if amenities:
        parts.append(f"Amenities: {amenities}")

    food = hotel.get("food_facility")
    if food:
        parts.append("Food: " + clean_text(food))

    suitable = clean_text(hotel.get("suitable_for"))
    if suitable:
        parts.append(f"Suitable for: {suitable}")

    ratings = hotel.get("ratings")
    if ratings:
        parts.append("Ratings: " + clean_text(ratings))

    booking = hotel.get("booking_links")
    if booking:
        parts.append("Booking: " + clean_text(booking))

    payment = clean_text(hotel.get("payment_modes"))
    if payment:
        parts.append(f"Payment: {payment}")

    landmarks = clean_text(hotel.get("nearby_landmarks"))
    if landmarks:
        parts.append(f"Nearby: {landmarks}")

    return "\n".join(parts)


def iter_hotels(data):
    hotels = data.get("hotels")
    if isinstance(hotels, list) and hotels:
        for hotel in hotels:
            yield hotel
        return
    yield data


def unique_doc_id(base, seen):
    if base not in seen:
        return base, False

    index = 2
    while f"{base}_{index}" in seen:
        index += 1
    return f"{base}_{index}", True


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(INPUT_DIR.rglob("*.json"))
    if not files:
        raise FileNotFoundError(f"No hotel JSON files in {INPUT_DIR}")

    documents = []
    seen = set()
    by_temple = {}
    duplicates = []

    for path in files:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        associated = (
            data.get("associated_temple")
            or data.get("associatedTemple")
            or ""
        )

        for hotel in iter_hotels(data):
            temple_id = (
                hotel.get("temple_id")
                or data.get("temple_id")
                or hotel.get("templeId")
                or data.get("templeId")
            )
            hotel_id = (
                hotel.get("hotel_id")
                or data.get("hotel_id")
                or hotel.get("hotelId")
            )
            name = hotel.get("hotel_name") or hotel.get("hotelName") or hotel_id

            if not temple_id or not hotel_id:
                raise ValueError(f"Missing temple_id/hotel_id in {path}")

            text = hotel_text(hotel, associated)
            if not text.strip():
                continue

            doc_id, was_duplicate = unique_doc_id(f"{temple_id}_{hotel_id}", seen)
            if was_duplicate:
                duplicates.append(f"{path.name} -> {doc_id}")

            seen.add(doc_id)
            by_temple[temple_id] = by_temple.get(temple_id, 0) + 1

            documents.append(
                {
                    "doc_id": doc_id,
                    "temple_id": temple_id,
                    "entity_type": "hotel",
                    "entity_id": hotel_id,
                    "section": "hotel",
                    "text": text,
                    "metadata": {
                        "hotel_name": name,
                        "associated_temple": associated,
                        "source_file": str(path.as_posix()),
                        "source_type": "hotel_record",
                    },
                }
            )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for document in documents:
            f.write(json.dumps(document, ensure_ascii=False) + "\n")

    print("Hotel normalization complete.")
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
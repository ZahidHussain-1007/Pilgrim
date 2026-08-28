import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TEMPLES_DIR = ROOT / "data" / "temples"
REGISTRY = ROOT / "data" / "temple_registry.json"
CHUNKS = ROOT / "processed" / "temple_chunks.jsonl"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def temple_name(data):
    return (
        data.get("name")
        or data.get("temple_name")
        or data.get("templeName")
        or ""
    )


def aliases(data):
    names = []
    names.extend(data.get("alternate_names") or [])
    names.extend(data.get("aliases") or [])
    multi = data.get("multilingual") or {}
    names.extend(multi.get("alternate_spellings") or [])
    lang = multi.get("names") or {}
    if isinstance(lang, dict):
        names.extend([v for v in lang.values() if v])
    loc = data.get("location") or {}
    for key in ("village", "mandal"):
        if loc.get(key):
            names.append(loc[key])
    cleaned = []
    seen = set()
    for name in names:
        if not isinstance(name, str):
            continue
        text = name.strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(text)
    return cleaned


def main():
    files = sorted(TEMPLES_DIR.glob("*.json"))
    print("=" * 80)
    print("PILGRIMAI TEMPLE CORPUS")
    print("=" * 80)
    print(f"Temple JSON files : {len(files)}")
    print(f"Folder            : {TEMPLES_DIR}")

    rows = []
    missing_id = []
    by_id = defaultdict(list)

    for path in files:
        data = load_json(path)
        temple_id = data.get("temple_id") or data.get("templeId")
        name = temple_name(data)
        if not temple_id:
            missing_id.append(path.name)
            continue
        by_id[temple_id].append(path.name)
        rows.append(
            {
                "file": path.name,
                "temple_id": temple_id,
                "name": name,
                "alias_count": len(aliases(data)),
            }
        )

    print("\n--- FILES ---")
    for row in sorted(rows, key=lambda x: x["temple_id"]):
        print(
            f"{row['temple_id']:<8} {row['alias_count']:>2} aliases | "
            f"{row['name'][:50]:<50} | {row['file']}"
        )

    print("\n--- ID PROBLEMS ---")
    print(f"Missing temple_id : {missing_id or 'none'}")
    dupes = {k: v for k, v in by_id.items() if len(v) > 1}
    print(f"Duplicate IDs     : {dupes or 'none'}")

    t0001 = [row for row in rows if row["temple_id"] == "T0001"]
    print("\n--- T0001 LOCK ---")
    if not t0001:
        print("FAIL : T0001 file missing")
    else:
        name = t0001[0]["name"].lower()
        ok = "yadadri" in name or "narasimha" in name or "yadagiri" in name
        print(f"{'PASS' if ok else 'FAIL'} : T0001 = {t0001[0]['name']}")

    print("\n--- REGISTRY vs FILES ---")
    registry_ids = set()
    if REGISTRY.exists():
        registry = load_json(REGISTRY)
        registry_ids = {item["temple_id"] for item in registry}
        print(f"Registry temples : {len(registry_ids)}")
        for item in registry:
            print(f"  {item['temple_id']} {item.get('name')}")
    else:
        print("Registry missing")

    file_ids = set(by_id)
    print(f"\nIn files, not registry : {sorted(file_ids - registry_ids) or 'none'}")
    print(f"In registry, not files : {sorted(registry_ids - file_ids) or 'none'}")

    print("\n--- CHUNKS ALREADY BUILT ---")
    chunk_ids = Counter()
    if CHUNKS.exists():
        with open(CHUNKS, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    chunk_ids[json.loads(line).get("temple_id")] += 1
        for temple_id, count in sorted(chunk_ids.items()):
            print(f"  {temple_id}: {count}")
        print(f"Indexed IDs : {sorted(chunk_ids)}")
        print(f"JSON only   : {sorted(file_ids - set(chunk_ids)) or 'none'}")
    else:
        print("processed/temple_chunks.jsonl missing")

    print("\n--- OTHER DATA ---")
    for folder in ("accommodations", "restaurants", "emergency"):
        found = list((ROOT / "data" / folder).rglob("*.json"))
        print(f"  {folder}: {len(found)} json files")

    print("\n" + "=" * 80)
    print(f"JSON temples : {len(file_ids)}")
    print(f"Registry     : {len(registry_ids)}")
    print(f"Chunked      : {len(chunk_ids)}")
    print("=" * 80)


if __name__ == "__main__":
    main()
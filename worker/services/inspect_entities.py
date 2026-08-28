import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def walk_json(folder):
    return sorted((ROOT / "data" / folder).rglob("*.json"))


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def temple_id_of(data, folder):
    if folder == "restaurants":
        assoc = data.get("associatedTemple") or {}
        return (
            data.get("temple_id")
            or data.get("templeId")
            or assoc.get("templeId")
            or assoc.get("temple_id")
        )
    if folder == "accommodations":
        hotels = data.get("hotels")
        if isinstance(hotels, list) and hotels:
            return (
                data.get("temple_id")
                or hotels[0].get("temple_id")
                or hotels[0].get("templeId")
            )
        return data.get("temple_id") or data.get("templeId")
    return data.get("temple_id") or data.get("templeId")


def main():
    print("=" * 80)
    print("PILGRIMAI ENTITY CORPUS")
    print("=" * 80)

    for folder in ("accommodations", "restaurants", "emergency"):
        files = walk_json(folder)
        ids = Counter()
        missing = []
        sample_keys = None

        for path in files:
            try:
                data = load(path)
            except Exception as error:
                print(f"BAD JSON {path}: {error}")
                continue
            if sample_keys is None:
                sample_keys = list(data.keys())[:20]
            temple_id = temple_id_of(data, folder)
            if temple_id:
                ids[temple_id] += 1
            else:
                missing.append(str(path.relative_to(ROOT / "data")))

        print(f"\n--- {folder} ---")
        print(f"files          : {len(files)}")
        print(f"sample keys    : {sample_keys}")
        print(f"missing temple : {len(missing)}")
        if missing[:8]:
            print("  ", missing[:8])
        print("per temple_id  :")
        for temple_id, count in sorted(ids.items()):
            print(f"  {temple_id}: {count}")
        print("unknown IDs    :", sorted(set(ids) - {f'T{i:04d}' for i in range(1, 24)}))

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
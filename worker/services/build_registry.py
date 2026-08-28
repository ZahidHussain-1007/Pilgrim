import json
import re
from collections import defaultdict
from pathlib import Path

from temple_resolver import normalize


ROOT = Path(__file__).resolve().parent.parent
TEMPLES_DIR = ROOT / "data" / "temples"
OUTPUT = ROOT / "data" / "temple_registry.json"


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def official_name(data):
    return (
        data.get("name")
        or data.get("temple_name")
        or data.get("templeName")
        or data["temple_id"]
    )


def raw_aliases(data):
    names = []
    names.extend(data.get("alternate_names") or [])
    names.extend(data.get("aliases") or [])
    multi = data.get("multilingual") or {}
    names.extend(multi.get("alternate_spellings") or [])
    lang = multi.get("names") or {}
    if isinstance(lang, dict) and lang.get("en"):
        names.append(lang["en"])
    return names


def expand_spellings(name: str) -> list:
    values = {name}
    changed = True

    while changed:
        changed = False
        for current in list(values):
            candidates = [
                re.sub(r"Saraswathi", "Saraswati", current, flags=re.I),
                re.sub(r"Saraswati", "Saraswathi", current, flags=re.I),
                re.sub(r"\bDevasthanam\b", "Temple", current, flags=re.I),
                re.sub(r"\bTemple\b", "Devasthanam", current, flags=re.I),
                re.sub(r"\bKashi\b", "Kasi", current, flags=re.I),
                re.sub(r"\bKasi\b", "Kashi", current, flags=re.I),
            ]
            for candidate in candidates:
                if candidate not in values:
                    values.add(candidate)
                    changed = True

    return list(values)


def clean_list(values):
    out = []
    seen = set()
    for value in values:
        if not isinstance(value, str):
            continue
        text = " ".join(value.split()).strip()
        key = normalize(text)
        if not key or len(key) < 4:
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


def main():
    files = sorted(TEMPLES_DIR.glob("T*.json"))
    temples = []
    village_owners = defaultdict(list)

    for path in files:
        data = load(path)
        temple_id = data["temple_id"]
        village = (data.get("location") or {}).get("village") or ""
        if village:
            village_owners[normalize(village)].append(temple_id)

        generated = []
        generated.append(official_name(data))
        generated.extend(raw_aliases(data))
        for item in list(generated):
            generated.extend(expand_spellings(item))

        aliases = clean_list(generated)
        official = official_name(data)
        aliases = [
            alias for alias in aliases
            if normalize(alias) != normalize(official)
        ]

        temples.append(
            {
                "temple_id": temple_id,
                "name": official,
                "aliases": aliases,
                "_village": village.strip(),
            }
        )

    for temple in temples:
        village = temple.pop("_village")
        key = normalize(village)
        if village and len(village_owners[key]) == 1:
            if normalize(village) != normalize(temple["name"]):
                if normalize(village) not in {normalize(a) for a in temple["aliases"]}:
                    temple["aliases"].append(village)

    alias_owners = defaultdict(set)
    for temple in temples:
        for name in [temple["name"], *temple["aliases"]]:
            alias_owners[normalize(name)].add(temple["temple_id"])

    collisions = {
        alias: sorted(ids)
        for alias, ids in alias_owners.items()
        if len(ids) > 1
    }

    OUTPUT.write_text(
        json.dumps(temples, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUTPUT}")
    print(f"Temples : {len(temples)}")
    print("\n--- SHARED NAMES (resolver must not guess) ---")
    if not collisions:
        print("none")
    else:
        for alias, ids in sorted(collisions.items(), key=lambda x: -len(x[0])):
            print(f"  {alias} -> {ids}")


if __name__ == "__main__":
    main()
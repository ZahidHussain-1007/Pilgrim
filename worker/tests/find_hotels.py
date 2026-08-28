"""Find where hotel JSON actually lives in this repo.

    python tests/find_hotels.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP = {
    ".venv",
    "venv",
    "qdrant_data",
    "node_modules",
    "__pycache__",
    ".git",
    "tests",
}


def interesting(name: str) -> bool:
    n = name.lower()
    return any(word in n for word in ("hotel", "lodge", "stay", "accom", "guest"))


def main() -> None:
    print("Project:", ROOT)
    data = ROOT / "data"
    if data.is_dir():
        print("\nFolders under data/:")
        for child in sorted(data.iterdir()):
            if child.is_dir():
                n_json = len(list(child.glob("*.json")))
                print(f"  {child.name:30}  {n_json} json files")
            else:
                print(f"  {child.name}  (file)")
    else:
        print("No data/ folder")

    hits: list[Path] = []
    for path in ROOT.rglob("*.json"):
        if any(part in SKIP for part in path.parts):
            continue
        if interesting(path.name) or interesting(str(path.parent)):
            hits.append(path)

    print(f"\nJSON paths whose name/folder looks like hotels: {len(hits)}")
    parents: dict[Path, int] = {}
    for path in hits:
        parents[path.parent] = parents.get(path.parent, 0) + 1
    for folder, count in sorted(parents.items(), key=lambda kv: (-kv[1], str(kv[0]))):
        print(f"  {count:4}  {folder}")

    sample = hits[0] if hits else None
    if sample is None:
        # last try: any json with hotel_id inside, scan data only
        print("\nScanning data/*.json for a hotel_id field (first 200 files)...")
        checked = 0
        for path in data.rglob("*.json") if data.is_dir() else []:
            checked += 1
            if checked > 200:
                break
            try:
                blob = path.read_text(encoding="utf-8", errors="ignore")[:4000]
            except OSError:
                continue
            if "hotel" in blob.lower():
                sample = path
                print("  found hotel text in", path)
                break
        print("  scanned", checked, "files")

    if sample is None:
        print("\nNo hotel JSON found. Tell me where those 142 hotel files are.")
        return

    print("\nSample file:", sample)
    try:
        data_obj = json.loads(sample.read_text(encoding="utf-8"))
    except Exception as exc:
        print("Could not parse:", exc)
        return
    record = data_obj[0] if isinstance(data_obj, list) and data_obj else data_obj
    if isinstance(record, dict):
        print("Top-level keys:")
        for key in record:
            val = record[key]
            preview = repr(val)
            if len(preview) > 120:
                preview = preview[:120] + "..."
            print(f"  {key}: {preview}")
    else:
        print("Unexpected JSON type:", type(record))


if __name__ == "__main__":
    main()

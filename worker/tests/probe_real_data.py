"""See what YOUR real data/ folder returns to budget/travel.

Run from project root:
    python tests/probe_real_data.py

Does not call Groq. Does not touch Qdrant.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.catalog import Catalog

DATA = ROOT / "data"


def main() -> None:
    if not (DATA / "temples").is_dir():
        print("No data/temples folder at", DATA / "temples")
        print("Run this from the project root: piligrimai_rag")
        raise SystemExit(1)

    cat = Catalog(DATA)
    print("data root :", DATA)
    print("temples   :", len(cat.temples), sorted(cat.temples))
    print("hotel files loaded :", len(cat.hotels))
    print("restaurant files   :", len(cat.restaurants))
    print("emergency files    :", len(cat.emergencies))
    print()

    costs = cat.get_costs("T0001")
    print("=== T0001 costs (what budget uses) ===")
    for row in costs["darshan"]:
        print(f"  darshan {row['code']}: fee={row['fee_inr']}  ({row['confidence']})")
    print(f"  temple_stay: {costs['temple_stay']}")
    print(f"  sevas with a number: {sum(1 for s in costs['sevas'] if s['fee_inr'] is not None or s['min_inr'] is not None)} / {len(costs['sevas'])}")
    print(f"  missing ({len(costs['missing'])}): {costs['missing'][:12]}")
    print()

    travel = cat.get_travel("T0001")
    print("=== T0001 travel (what travel uses) ===")
    print(f"  lat,lng = {travel['lat']}, {travel['lng']}")
    print(f"  hyd_km  = {travel['road_from_hyderabad_km']}")
    print(f"  rail    = {travel['nearest_railway']}")
    print()

    for tid, label in (("T0001", "Yadadri"), ("T0020", "Beechupally")):
        hotels = cat.get_hotels(tid)
        priced = [h for h in hotels["items"] if h["min_inr"] is not None]
        print(f"=== {tid} {label} hotels: {len(hotels['items'])} found, {len(priced)} have a rupee number ===")
        for h in hotels["items"][:8]:
            print(f"  {h['entity_id']:20}  ₹{h['min_inr']}-{h['max_inr']}  {h['name'][:50]}")
        if len(hotels["items"]) > 8:
            print(f"  ... +{len(hotels['items']) - 8} more")
        print()

    print("Send this whole print to me. Especially the hotel counts.")


if __name__ == "__main__":
    main()

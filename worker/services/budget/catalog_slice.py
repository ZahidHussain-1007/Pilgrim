"""Read catalog JSON. Never invent a fee."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def load_catalog_slice(temple_id: str, data_root: str | Path | None = None) -> dict[str, Any]:
    from services.catalog import Catalog, CatalogError, find_data_root

    empty = {
        "darshan": [],
        "sevas": [],
        "hotels": [],
        "restaurants": [],
        "road_km": None,
        "temple_name": None,
        "free_meals": False,
        "error": None,
    }
    try:
        root = Path(data_root) if data_root else find_data_root()
        cat = Catalog(root)
        costs = cat.get_costs(temple_id)
        hotels = cat.get_hotels(temple_id)
        food = cat.get_restaurants(temple_id)
        travel = cat.get_travel(temple_id)
        temple = cat.temples.get(str(temple_id).strip().upper()) or {}
    except (CatalogError, FileNotFoundError, OSError) as exc:
        empty["error"] = str(exc)
        return empty

    stay = costs.get("temple_stay") or {}
    hotel_rows = list(hotels.get("items") or [])
    if stay.get("min_inr") is not None or stay.get("max_inr") is not None:
        hotel_rows.append(
            {
                "name": "temple-managed rooms",
                "min_inr": stay.get("min_inr"),
                "max_inr": stay.get("max_inr"),
            }
        )
    blob = json.dumps(temple, ensure_ascii=False).lower()
    return {
        "darshan": list(costs.get("darshan") or []),
        "sevas": list(costs.get("sevas") or []),
        "hotels": hotel_rows,
        "restaurants": list(food.get("items") or []),
        "road_km": travel.get("road_from_hyderabad_km"),
        "temple_name": costs.get("temple_name") or temple.get("name"),
        "free_meals": bool(re.search(r"annadanam|free meals", blob)),
        "error": None,
        "missing": list(costs.get("missing") or [])
        + list(hotels.get("missing") or [])
        + list(food.get("missing") or []),
    }

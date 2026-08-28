"""Structured fact catalog for budget + travel agents.

Reads source JSON only. No Groq. No vector search.
Chat stays in ask(). Agents call these getters.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


INR_PAIR = re.compile(
    r"(?:₹|rs\.?|inr)\s*([0-9][0-9,]*)(?:\s*(?:-|–|to|and)\s*(?:₹|rs\.?|inr)?\s*([0-9][0-9,]*))?",
    re.I,
)
BARE_PAIR = re.compile(
    r"\b([0-9][0-9,]*)\s*(?:-|–|to|and)\s*([0-9][0-9,]*)\b",
    re.I,
)
KM = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*km", re.I)
FREE = re.compile(r"\b(free|no\s+entry\s+fee|no\s+charge)\b", re.I)
PAID_UNKNOWN = re.compile(r"\b(paid|confirm\s+current\s+fee|amount\s+not\s+specified)\b", re.I)


def _num(value: Any) -> int | float | None:
    if value is None or value is False:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value) if float(value).is_integer() else float(value)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(",", "")
    try:
        number = float(text)
    except ValueError:
        return None
    return int(number) if number.is_integer() else number


def _inr_from_text(text: Any) -> tuple[int | None, int | None]:
    if text is None:
        return None, None
    if isinstance(text, (int, float)) and not isinstance(text, bool):
        n = int(text)
        return n, n
    blob = str(text)
    if not blob.strip():
        return None, None
    # "9:00–10:00 AM" is a clock, not rupees
    blob = re.sub(r"\d{1,2}:\d{2}", " ", blob)
    match = INR_PAIR.search(blob)
    if match:
        lo = int(match.group(1).replace(",", ""))
        hi = int(match.group(2).replace(",", "")) if match.group(2) else lo
        return min(lo, hi), max(lo, hi)
    match = BARE_PAIR.search(blob)
    if match and re.search(r"(₹|rs\.?|inr|price|cost|tariff|night|fee)", blob, re.I):
        lo = int(match.group(1).replace(",", ""))
        hi = int(match.group(2).replace(",", ""))
        return min(lo, hi), max(lo, hi)
    return None, None


def _charge_to_price(charges: Any) -> dict[str, Any]:
    if charges is None or charges == "":
        return {"fee_inr": None, "min_inr": None, "max_inr": None, "confidence": "unknown"}
    if isinstance(charges, (int, float)) and not isinstance(charges, bool):
        fee = int(charges)
        return {"fee_inr": fee, "min_inr": fee, "max_inr": fee, "confidence": "listed"}
    if isinstance(charges, dict):
        fee = _num(charges.get("fee_inr") or charges.get("amount") or charges.get("price"))
        lo = _num(charges.get("min_inr") or charges.get("min"))
        hi = _num(charges.get("max_inr") or charges.get("max"))
        if fee is not None:
            return {"fee_inr": int(fee), "min_inr": int(fee), "max_inr": int(fee), "confidence": "listed"}
        if lo is not None or hi is not None:
            return {
                "fee_inr": None,
                "min_inr": int(lo) if lo is not None else None,
                "max_inr": int(hi) if hi is not None else None,
                "confidence": "range" if lo is not None and hi is not None else "listed",
            }
        return _charge_to_price(charges.get("text") or charges.get("note") or "")
    blob = str(charges)
    if FREE.search(blob) and not PAID_UNKNOWN.search(blob):
        return {"fee_inr": 0, "min_inr": 0, "max_inr": 0, "confidence": "official"}
    lo, hi = _inr_from_text(blob)
    if lo is not None and hi is not None and lo == hi:
        return {"fee_inr": lo, "min_inr": lo, "max_inr": hi, "confidence": "listed"}
    if lo is not None or hi is not None:
        return {"fee_inr": None, "min_inr": lo, "max_inr": hi, "confidence": "range"}
    if PAID_UNKNOWN.search(blob) or blob.strip().lower() in {"paid", "n/a", "na", "unknown"}:
        return {"fee_inr": None, "min_inr": None, "max_inr": None, "confidence": "unknown"}
    return {"fee_inr": None, "min_inr": None, "max_inr": None, "confidence": "unknown"}


def _first(*values: Any) -> Any:
    for value in values:
        if value is None or value is False:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_json_files(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.rglob("*.json") if p.is_file())


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _temple_ids_of(record: dict[str, Any]) -> set[str]:
    found: set[str] = set()
    for key in ("temple_id", "templeId"):
        val = record.get(key)
        if isinstance(val, str) and val.strip():
            found.add(val.strip().upper())
        if isinstance(val, list):
            found.update(str(x).strip().upper() for x in val if x)
    for key in ("temple_ids", "linked_temples", "nearby_temples"):
        for item in _as_list(record.get(key)):
            if isinstance(item, str) and item.strip():
                found.add(item.strip().upper())
            elif isinstance(item, dict):
                tid = item.get("temple_id") or item.get("id")
                if tid:
                    found.add(str(tid).strip().upper())
    temple = record.get("temple")
    if isinstance(temple, str) and re.fullmatch(r"T\d{4}", temple.strip(), re.I):
        found.add(temple.strip().upper())
    elif isinstance(temple, dict):
        tid = temple.get("temple_id") or temple.get("id")
        if tid:
            found.add(str(tid).strip().upper())
    return found


def _entity_id(record: dict[str, Any], fallback: str) -> str:
    for key in ("entity_id", "hotel_id", "restaurant_id", "place_id", "id"):
        val = record.get(key)
        if isinstance(val, str) and val.strip() and not re.fullmatch(r"T\d{4}", val.strip(), re.I):
            return val.strip()
    return fallback


def _name_of(record: dict[str, Any]) -> str:
    name = _first(record.get("name"), record.get("hotel_name"), record.get("restaurant_name"), record.get("title"))
    return str(name).strip() if name else "Unknown"


def _distance_km(record: dict[str, Any]) -> float | None:
    for key in ("distance_km", "distanceKm", "km"):
        n = _num(record.get(key))
        if n is not None:
            return float(n)
    for key in ("distance", "distance_from_temple", "approx_distance"):
        val = record.get(key)
        n = _num(val)
        if n is not None:
            return float(n)
        if isinstance(val, str):
            match = KM.search(val)
            if match:
                return float(match.group(1))
    return None


def _place_prices(record: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "min_inr",
        "max_inr",
        "price_min",
        "price_max",
        "min_price",
        "max_price",
        "tariff_min",
        "tariff_max",
    ):
        pass
    lo = _num(
        _first(
            record.get("min_inr"),
            record.get("price_min"),
            record.get("min_price"),
            record.get("tariff_min"),
        )
    )
    hi = _num(
        _first(
            record.get("max_inr"),
            record.get("price_max"),
            record.get("max_price"),
            record.get("tariff_max"),
        )
    )
    if lo is None and hi is None and isinstance(record.get("price"), (int, float)):
        lo = hi = int(record["price"])
    free_blob = " ".join(
        str(record.get(k) or "")
        for k in ("price", "price_range", "charges", "cost", "note", "name")
    )
    if lo is None and hi is None and FREE.search(free_blob):
        return {
            "min_inr": 0,
            "max_inr": 0,
            "confidence": "official",
            "last_verified": record.get("last_verified") or record.get("verified_on"),
        }
    if lo is None or hi is None:
        blob = _first(
            record.get("price_range"),
            record.get("price"),
            record.get("tariff"),
            record.get("tariff_range"),
            record.get("room_tariff"),
            record.get("room_rent"),
            record.get("price_per_night"),
            record.get("cost_per_night"),
            record.get("starting_from"),
            record.get("approx_tariff"),
            record.get("charges"),
            record.get("approx_price"),
            record.get("cost"),
            record.get("rates"),
            record.get("rent"),
        )
        tlo, thi = _inr_from_text(blob)
        lo = lo if lo is not None else tlo
        hi = hi if hi is not None else thi
    if lo is not None:
        lo = int(lo)
    if hi is not None:
        hi = int(hi)
    if lo is not None and hi is not None and lo > hi:
        lo, hi = hi, lo
    if lo is None and hi is None:
        confidence = "unknown"
    elif lo is not None and hi is not None and lo != hi:
        confidence = "range"
    else:
        confidence = "listed"
    return {
        "min_inr": lo,
        "max_inr": hi,
        "confidence": confidence,
        "last_verified": record.get("last_verified") or record.get("verified_on"),
    }


def _unique_by_id(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for row in rows:
        seen.setdefault(row["entity_id"], row)
    return list(seen.values())


def _km_from_text(text: Any) -> float | None:
    if text is None:
        return None
    n = _num(text)
    if n is not None:
        return float(n)
    match = KM.search(str(text))
    return float(match.group(1)) if match else None


def _station(name: Any, km: Any = None) -> dict[str, Any] | None:
    if not name:
        return None
    return {"name": str(name).strip(), "km": _km_from_text(km)}


class CatalogError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


class Catalog:
    def __init__(self, data_root: str | Path):
        self.data_root = Path(data_root)
        self.temples: dict[str, dict[str, Any]] = {}
        self.hotels: list[dict[str, Any]] = []
        self.restaurants: list[dict[str, Any]] = []
        self.emergencies: list[dict[str, Any]] = []
        self.reload()

    def reload(self) -> None:
        self.temples = {}
        for path in _iter_json_files(self.data_root / "temples"):
            try:
                data = _read_json(path)
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(data, dict):
                continue
            tid = str(data.get("temple_id") or path.stem).strip().upper()
            if not re.fullmatch(r"T\d{4}", tid):
                continue
            data["temple_id"] = tid
            data["_source_path"] = str(path)
            self.temples[tid] = data
        self.hotels = []
        for folder_name in ("hotels", "accommodations", "accommodation"):
            self.hotels.extend(self._load_places(self.data_root / folder_name, kind="hotel"))
        self.restaurants = self._load_places(self.data_root / "restaurants", kind="restaurant")
        self.emergencies = self._load_places(self.data_root / "emergency", kind="emergency")

    def _load_places(self, folder: Path, kind: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for path in _iter_json_files(folder):
            try:
                data = _read_json(path)
            except (OSError, json.JSONDecodeError):
                continue
            records = data if isinstance(data, list) else [data]
            for index, record in enumerate(records):
                if not isinstance(record, dict):
                    continue
                rows.extend(self._expand_record(record, path, kind, index))
        return rows

    def _expand_record(self, record: dict[str, Any], path: Path, kind: str, index: int) -> list[dict[str, Any]]:
        record = dict(record)
        parent_ids = _temple_ids_of(record)
        file_id = record.get("hotel_id") or record.get("restaurant_id") or path.stem
        nested_key = None
        if kind == "hotel" and isinstance(record.get("hotels"), list) and record["hotels"]:
            nested_key = "hotels"
        elif kind == "restaurant" and isinstance(record.get("restaurants"), list) and record["restaurants"]:
            nested_key = "restaurants"
        if nested_key:
            rows: list[dict[str, Any]] = []
            for inner_index, inner in enumerate(record[nested_key]):
                if not isinstance(inner, dict):
                    continue
                child = dict(inner)
                child["_kind"] = kind
                child["_source_path"] = str(path)
                child["_temple_ids"] = _temple_ids_of(child) or set(parent_ids)
                child["_entity_id"] = _entity_id(child, f"{file_id}_{inner_index}")
                if not child["_temple_ids"] and record.get("temple_id"):
                    child["_temple_ids"] = {str(record["temple_id"]).strip().upper()}
                rows.append(child)
            return rows
        record["_kind"] = kind
        record["_source_path"] = str(path)
        record["_temple_ids"] = parent_ids
        record["_entity_id"] = _entity_id(record, f"{path.stem}_{index}")
        return [record]

    def _require(self, temple_id: str | None) -> dict[str, Any]:
        if not temple_id or not str(temple_id).strip():
            raise CatalogError("missing_temple_id", "temple_id is required", 422)
        tid = str(temple_id).strip().upper()
        if not re.fullmatch(r"T\d{4}", tid):
            raise CatalogError(
                "use_temple_id",
                "Send a resolved temple_id like T0001. Do not send a nickname.",
                409,
            )
        temple = self.temples.get(tid)
        if temple is None:
            raise CatalogError("unknown_temple", f"No temple {tid} in catalog", 404)
        return temple

    def _envelope(self, temple: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
        body = {
            "temple_id": temple["temple_id"],
            "temple_name": temple.get("name"),
            "last_verified": temple.get("last_verified"),
        }
        body.update(extra)
        return body

    def get_temple(self, temple_id: str) -> dict[str, Any]:
        temple = self._require(temple_id)
        loc = temple.get("location") or {}
        contact = temple.get("contact") or {}
        return {
            "temple_id": temple["temple_id"],
            "name": temple.get("name"),
            "district": loc.get("district"),
            "pincode": loc.get("pincode"),
            "lat": loc.get("latitude"),
            "lng": loc.get("longitude"),
            "official_website": contact.get("official_website"),
            "last_verified": temple.get("last_verified"),
        }

    def get_costs(self, temple_id: str) -> dict[str, Any]:
        temple = self._require(temple_id)
        darshan: list[dict[str, Any]] = []
        tickets = temple.get("darshan_and_tickets") or {}
        if tickets:
            general = _charge_to_price(tickets.get("general_darshan") or "Free")
            darshan.append(
                {
                    "code": "sarva",
                    "name": "Sarva Darshan",
                    "fee_inr": general["fee_inr"],
                    "confidence": general["confidence"],
                    "note": None if general["fee_inr"] == 0 else str(tickets.get("general_darshan") or "") or None,
                }
            )
            special = _charge_to_price(tickets.get("special_darshan"))
            darshan.append(
                {
                    "code": "vip_break",
                    "name": "VIP Break / Seegra Darshan",
                    "fee_inr": special["fee_inr"],
                    "confidence": special["confidence"],
                    "note": str(tickets.get("special_darshan") or "") or None,
                }
            )
        sevas: list[dict[str, Any]] = []
        for seva in _as_list(temple.get("sevas")):
            if not isinstance(seva, dict):
                continue
            price = _charge_to_price(seva.get("charges") if "charges" in seva else seva.get("price"))
            name = str(seva.get("name") or "Unnamed seva").strip()
            code = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
            if "sarva" in code and "darshan" in code:
                if not any(d["code"] == "sarva" for d in darshan):
                    darshan.append(
                        {
                            "code": "sarva",
                            "name": name,
                            "fee_inr": price["fee_inr"],
                            "confidence": price["confidence"],
                            "note": None,
                        }
                    )
                continue
            sevas.append(
                {
                    "name": name,
                    "fee_inr": price["fee_inr"],
                    "min_inr": price["min_inr"],
                    "max_inr": price["max_inr"],
                    "confidence": price["confidence"],
                }
            )

        stay_src = temple.get("accommodation") or {}
        stay_price = _charge_to_price(stay_src.get("price_range"))
        temple_stay = {
            "min_inr": stay_price["min_inr"],
            "max_inr": stay_price["max_inr"],
            "unit": "night",
            "confidence": stay_price["confidence"] if stay_src else "unknown",
        }

        missing: list[str] = []
        for item in darshan:
            if item["fee_inr"] is None:
                missing.append(f"{item['code']}.fee_inr")
        for item in sevas:
            if item["fee_inr"] is None and item["min_inr"] is None:
                missing.append(f"{item['name']}.fee_inr")
        if temple_stay["min_inr"] is None:
            missing.append("temple_stay.min_inr")

        return self._envelope(
            temple,
            {
                "currency": "INR",
                "darshan": darshan,
                "sevas": sevas,
                "temple_stay": temple_stay,
                "missing": missing,
            },
        )

    def get_hotels(self, temple_id: str) -> dict[str, Any]:
        return self._places(temple_id, self.hotels, "hotels")

    def get_restaurants(self, temple_id: str) -> dict[str, Any]:
        return self._places(temple_id, self.restaurants, "restaurants")

    def get_emergency(self, temple_id: str) -> dict[str, Any]:
        temple = self._require(temple_id)
        rows: list[dict[str, Any]] = []
        for record in self.emergencies:
            if temple["temple_id"] not in record["_temple_ids"]:
                continue
            kind = (
                record.get("service_type")
                or record.get("category")
                or record.get("type")
                or record.get("section")
                or "emergency"
            )
            rows.append(
                {
                    "entity_id": record["_entity_id"],
                    "name": _name_of(record),
                    "kind": str(kind).lower(),
                    "phone": _first(record.get("phone"), record.get("phone_number"), record.get("contact")),
                    "distance_km": _distance_km(record),
                }
            )
        items = _unique_by_id(rows)
        missing = [] if items else ["emergency"]
        return self._envelope(temple, {"items": items, "missing": missing})

    def get_travel(self, temple_id: str) -> dict[str, Any]:
        temple = self._require(temple_id)
        loc = temple.get("location") or {}
        travel = temple.get("travel") or {}
        hyd_km = None
        for line in _as_list(travel.get("distances")):
            text = str(line)
            if re.search(r"hyderabad", text, re.I):
                hyd_km = _km_from_text(text)
                break
        if hyd_km is None:
            hyd_km = _km_from_text(travel.get("road"))

        rail = travel.get("nearest_railway_station")
        bus = travel.get("nearest_bus_station")
        air = travel.get("nearest_airport")
        rail_obj = _station(rail, rail) if not isinstance(rail, dict) else _station(rail.get("name"), rail.get("km"))
        bus_obj = _station(bus, bus) if not isinstance(bus, dict) else _station(bus.get("name"), bus.get("km"))
        air_obj = _station(air, air) if not isinstance(air, dict) else _station(air.get("name"), air.get("km"))

        missing = []
        if loc.get("latitude") is None or loc.get("longitude") is None:
            missing.append("lat_lng")
        if hyd_km is None:
            missing.append("road_from_hyderabad_km")

        return self._envelope(
            temple,
            {
                "lat": loc.get("latitude"),
                "lng": loc.get("longitude"),
                "road_from_hyderabad_km": hyd_km,
                "nearest_railway": rail_obj,
                "nearest_airport": air_obj,
                "nearest_bus": bus_obj,
                "missing": missing,
            },
        )

    def _places(self, temple_id: str, pool: list[dict[str, Any]], label: str) -> dict[str, Any]:
        temple = self._require(temple_id)
        rows: list[dict[str, Any]] = []
        for record in pool:
            if temple["temple_id"] not in record["_temple_ids"]:
                continue
            price = _place_prices(record)
            rows.append(
                {
                    "entity_id": record["_entity_id"],
                    "name": _name_of(record),
                    "distance_km": _distance_km(record),
                    "min_inr": price["min_inr"],
                    "max_inr": price["max_inr"],
                    "unit": "night" if label == "hotels" else None,
                    "confidence": price["confidence"],
                    "last_verified": price["last_verified"] or temple.get("last_verified"),
                }
            )
        items = _unique_by_id(rows)
        missing = [] if items else [label]
        if any(i["min_inr"] is None for i in items):
            missing.append(f"{label}_without_price")
        return self._envelope(temple, {"items": items, "missing": missing})


_CATALOG: Catalog | None = None


def find_data_root(start: Path | None = None) -> Path:
    here = (start or Path(__file__)).resolve()
    candidates = [here.parent, here.parent.parent, Path.cwd()]
    for base in candidates:
        for option in (base / "data", base / "tests" / "fixtures"):
            if (option / "temples").is_dir():
                return option
    raise FileNotFoundError("data/temples not found. Pass Catalog(data_root=...)")


def get_catalog(data_root: str | Path | None = None) -> Catalog:
    global _CATALOG
    if data_root is not None:
        _CATALOG = Catalog(data_root)
        return _CATALOG
    if _CATALOG is None:
        _CATALOG = Catalog(find_data_root())
    return _CATALOG


def get_temple(temple_id: str) -> dict[str, Any]:
    return get_catalog().get_temple(temple_id)


def get_costs(temple_id: str) -> dict[str, Any]:
    return get_catalog().get_costs(temple_id)


def get_hotels(temple_id: str) -> dict[str, Any]:
    return get_catalog().get_hotels(temple_id)


def get_restaurants(temple_id: str) -> dict[str, Any]:
    return get_catalog().get_restaurants(temple_id)


def get_travel(temple_id: str) -> dict[str, Any]:
    return get_catalog().get_travel(temple_id)


def get_emergency(temple_id: str) -> dict[str, Any]:
    return get_catalog().get_emergency(temple_id)

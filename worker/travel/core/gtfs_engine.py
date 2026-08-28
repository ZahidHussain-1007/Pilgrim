from __future__ import annotations

import csv
import math
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Optional


class GTFSLoader:
    def __init__(self, routes_path: str, trips_path: str, stop_times_path: str, stops_path: str):
        self.routes_path = Path(routes_path)
        self.trips_path = Path(trips_path)
        self.stop_times_path = Path(stop_times_path)
        self.stops_path = Path(stops_path)

    def read_csv(self, path: str):
        with open(path, newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))

    def load(self):
        routes = self.read_csv(str(self.routes_path))
        trips = self.read_csv(str(self.trips_path))
        stop_times = self.read_csv(str(self.stop_times_path))
        stops = self.read_csv(str(self.stops_path))
        return {
            "routes": routes,
            "trips": trips,
            "stop_times": stop_times,
            "stops": stops,
        }


class GTFSPlanner:
    def __init__(self, gtfs_data: Dict[str, List[Dict[str, str]]]):
        self.data = gtfs_data
        self.stops = gtfs_data.get("stops", [])
        self.stop_by_id = {row.get("stop_id"): row for row in self.stops if row.get("stop_id")}
        self.trip_by_id = {row.get("trip_id"): row for row in gtfs_data.get("trips", []) if row.get("trip_id")}
        self.route_by_id = {row.get("route_id"): row for row in gtfs_data.get("routes", []) if row.get("route_id")}
        self.graph = defaultdict(list)
        self._build_graph()

    def _normalize_name(self, value: str) -> str:
        return "".join(ch.lower() for ch in (value or "") if ch.isalnum())

    def _build_graph(self):
        trip_stop_rows = defaultdict(list)
        for row in self.data.get("stop_times", []):
            trip_id = row.get("trip_id")
            stop_id = row.get("stop_id")
            if not trip_id or not stop_id or trip_id not in self.trip_by_id:
                continue
            try:
                seq = int(float(row.get("stop_sequence", "0")))
            except (TypeError, ValueError):
                continue
            trip_stop_rows[trip_id].append((seq, row))

        for trip_id, rows in trip_stop_rows.items():
            rows.sort(key=lambda item: item[0])
            trip = self.trip_by_id.get(trip_id, {})
            route_id = trip.get("route_id")
            direction_id = trip.get("direction_id", "")
            route = self.route_by_id.get(route_id, {})
            mode = self._route_mode(route.get("route_type"))
            for index in range(len(rows) - 1):
                current = rows[index][1]
                nxt = rows[index + 1][1]
                current_stop = current.get("stop_id")
                next_stop = nxt.get("stop_id")
                if not current_stop or not next_stop:
                    continue
                self.graph[current_stop].append(
                    {
                        "to": next_stop,
                        "route_id": route_id,
                        "route_name": route.get("route_long_name") or route.get("route_short_name") or route_id,
                        "mode": mode,
                        "direction_id": direction_id,
                        "trip_id": trip_id,
                        "departure_time": current.get("departure_time"),
                        "arrival_time": nxt.get("arrival_time"),
                    }
                )

    def _route_mode(self, route_type: str | None) -> str:
        modes = {
            "0": "tram",
            "1": "subway",
            "2": "train",
            "3": "bus",
            "4": "ferry",
            "5": "cable_car",
            "6": "gondola",
            "7": "funicular",
        }
        return modes.get(str(route_type or ""), "transit")

    def _distance_km(self, first_stop_id: str, second_stop_id: str) -> float:
        first = self.stop_by_id.get(first_stop_id, {})
        second = self.stop_by_id.get(second_stop_id, {})
        try:
            lat1, lon1 = float(first["stop_lat"]), float(first["stop_lon"])
            lat2, lon2 = float(second["stop_lat"]), float(second["stop_lon"])
        except (KeyError, TypeError, ValueError):
            return 0.0
        latitude_delta = math.radians(lat2 - lat1)
        longitude_delta = math.radians(lon2 - lon1)
        first_latitude, second_latitude = math.radians(lat1), math.radians(lat2)
        haversine = (
            math.sin(latitude_delta / 2) ** 2
            + math.cos(first_latitude) * math.cos(second_latitude) * math.sin(longitude_delta / 2) ** 2
        )
        return 6371.0 * 2 * math.atan2(math.sqrt(haversine), math.sqrt(1 - haversine))

    def _build_segments(self, path, edges):
        segments = []
        for edge in edges:
            from_stop_id = segments[-1]["to_stop_id"] if segments else path[0]
            segment = {
                "from_stop_id": from_stop_id,
                "to_stop_id": edge["to"],
                "route_id": edge.get("route_id"),
                "route_name": edge.get("route_name"),
                "mode": edge.get("mode", "transit"),
                "distance_km": self._distance_km(from_stop_id, edge["to"]),
                "trip_id": edge.get("trip_id"),
                "departure_time": edge.get("departure_time"),
                "arrival_time": edge.get("arrival_time"),
            }
            if segments and all(
                segment[key] == segments[-1][key] for key in ("route_id", "mode", "route_name", "trip_id")
            ):
                segments[-1]["to_stop_id"] = segment["to_stop_id"]
                segments[-1]["distance_km"] += segment["distance_km"]
                segments[-1]["arrival_time"] = segment["arrival_time"]
            else:
                segments.append(segment)
        return segments

    def find_stop_matches(self, place_name: str, limit: int = 5):
        if not place_name:
            return []
        normalized = self._normalize_name(place_name)
        matches = []
        for stop in self.stops:
            name = (stop.get("stop_name") or "").strip()
            normalized_name = self._normalize_name(name)
            if normalized == normalized_name:
                score = 1.0
            elif normalized in normalized_name or normalized_name in normalized:
                score = 0.8
            elif any(token in normalized_name for token in normalized.split()):
                score = 0.6
            else:
                score = 0.0
            if score > 0:
                matches.append({**stop, "score": score})
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:limit]

    def _time_minutes(self, value: Optional[str]) -> Optional[int]:
        if not value:
            return None
        try:
            hours, minutes, *_ = value.split(":")
            return int(hours) * 60 + int(minutes)
        except (TypeError, ValueError):
            return None

    def find_candidate_routes(
        self,
        source: str,
        destination: str,
        limit: int = 10,
        mode: str = "transit",
        departure_time: Optional[str] = None,
    ):
        source_matches = self.find_stop_matches(source)
        destination_matches = self.find_stop_matches(destination)
        if not source_matches or not destination_matches:
            return []

        candidates = []
        max_hops = 80
        max_queue = 8000
        for source_row in source_matches[:3]:
            for destination_row in destination_matches[:3]:
                source_id = source_row.get("stop_id")
                destination_id = destination_row.get("stop_id")
                if not source_id or not destination_id:
                    continue
                found = self._bfs_routes(
                    source_id,
                    destination_id,
                    limit=limit,
                    mode=mode,
                    departure_time=departure_time,
                    max_hops=max_hops,
                    max_queue=max_queue,
                )
                candidates.extend(found)
                if len(candidates) >= limit:
                    return candidates[:limit]
        return candidates[:limit]

    def _bfs_routes(
        self,
        source_id: str,
        destination_id: str,
        limit: int,
        mode: str,
        departure_time: Optional[str],
        max_hops: int,
        max_queue: int,
    ):
        if source_id == destination_id:
            return []
        candidates = []
        queue = deque([(source_id, [source_id], [], {source_id})])

        while queue and len(candidates) < limit:
            if len(queue) > max_queue:
                break
            current_stop, path, edges, visited = queue.popleft()
            if len(path) > max_hops:
                continue

            if current_stop == destination_id and len(path) > 1:
                first_departure = self._time_minutes(edges[0].get("departure_time"))
                final_arrival = self._time_minutes(edges[-1].get("arrival_time"))
                requested_departure = self._time_minutes(departure_time)
                if (
                    requested_departure is not None
                    and first_departure is not None
                    and first_departure < requested_departure
                ):
                    continue
                candidate = {
                    "path": path,
                    "edges": edges,
                    "segments": self._build_segments(path, edges),
                    "transfers": max(0, len({edge["route_id"] for edge in edges}) - 1),
                    "mode_changes": sum(
                        1
                        for previous, current in zip(edges, edges[1:])
                        if previous.get("mode") != current.get("mode")
                    ),
                    "distance_km": sum(self._distance_km(left, right) for left, right in zip(path, path[1:])),
                    "departure_time": edges[0].get("departure_time"),
                    "arrival_time": edges[-1].get("arrival_time"),
                    "duration_minutes": (
                        final_arrival - first_departure
                        if first_departure is not None and final_arrival is not None
                        else None
                    ),
                }
                candidates.append(candidate)
                continue

            for edge in self.graph.get(current_stop, []):
                if mode not in ("transit", "bus") and edge.get("mode") != mode:
                    continue
                if edges:
                    previous_arrival = self._time_minutes(edges[-1].get("arrival_time"))
                    next_departure = self._time_minutes(edge.get("departure_time"))
                    if (
                        previous_arrival is not None
                        and next_departure is not None
                        and next_departure < previous_arrival
                    ):
                        continue
                next_stop = edge["to"]
                if next_stop in visited:
                    continue
                next_path = path + [next_stop]
                next_edges = edges + [edge]
                next_visited = set(visited)
                next_visited.add(next_stop)
                queue.append((next_stop, next_path, next_edges, next_visited))

        return candidates

    def recommend_route(self, candidates, preference: str = "balanced"):
        if not candidates:
            return None

        scored = []
        for route in candidates:
            transfers = route["transfers"]
            distance = route["distance_km"]
            duration = route.get("duration_minutes")
            duration_score = duration if duration is not None else 100000
            if preference == "fastest":
                score = duration_score * 100 + transfers * 10 + distance
            elif preference == "fewest_transfers":
                score = transfers * 10000 + (duration_score * 10) + distance
            else:
                score = (transfers * 1000) + (duration_score * 2) + (distance * 10)
            scored.append({**route, "score": score})

        scored.sort(key=lambda item: item["score"])
        best = scored[0]
        return {
            "path": best["path"],
            "transfers": best["transfers"],
            "distance_km": best["distance_km"],
            "score": best["score"],
            "segments": best["segments"],
            "mode_changes": best["mode_changes"],
            "departure_time": best.get("departure_time"),
            "arrival_time": best.get("arrival_time"),
            "duration_minutes": best.get("duration_minutes"),
        }

    def plan_route(
        self,
        source: str,
        destination: str,
        mode: str = "transit",
        departure_time: Optional[str] = None,
        preference: str = "balanced",
    ):
        candidates = self.find_candidate_routes(
            source, destination, mode=mode, departure_time=departure_time
        )
        if not candidates:
            return None

        best = self.recommend_route(candidates, preference=preference)
        if not best:
            return None

        route = {
            "route_id": "multi-route",
            "summary": (
                f"Recommended GTFS route from {source} to {destination} using {mode}; "
                f"{best['transfers']} transfer(s)"
            ),
            "segments": best["segments"],
            "confidence": 0.8,
            "path": best["path"],
            "transfers": best["transfers"],
            "distance_km": best["distance_km"],
            "mode_changes": best["mode_changes"],
            "duration_minutes": best.get("duration_minutes"),
            "departure_time": best.get("departure_time"),
            "arrival_time": best.get("arrival_time"),
            "alternatives": [candidate for candidate in candidates if candidate.get("path") != best.get("path")],
        }
        return route

    def plan_from_gtfs(
        self,
        source: str,
        destination: str,
        mode: str = "transit",
        departure_time: Optional[str] = None,
        preference: str = "balanced",
    ):
        return self.plan_route(source, destination, mode, departure_time, preference)

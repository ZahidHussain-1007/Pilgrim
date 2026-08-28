import json
import re
from difflib import SequenceMatcher
from pathlib import Path


REGISTRY_PATH = Path(__file__).resolve().parent.parent / "data" / "temple_registry.json"

FUZZY_MIN_ALIAS = 6
FUZZY_THRESHOLD = 0.8


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


class TempleResolver:

    def __init__(self, registry_path=REGISTRY_PATH):
        with open(registry_path, encoding="utf-8") as f:
            self.temples = json.load(f)

        self.meta = {item["temple_id"]: item for item in self.temples}
        self.alias_map = {}

        for temple in self.temples:
            temple_id = temple["temple_id"]
            names = [temple["name"], *temple.get("aliases", [])]
            for name in names:
                key = normalize(name)
                if not key or len(key) < 4:
                    continue
                bucket = self.alias_map.setdefault(key, [])
                if temple_id not in bucket:
                    bucket.append(temple_id)

    def aliases_for(self, temple_id: str) -> list:
        temple = self.meta.get(temple_id)
        if not temple:
            return []
        return [temple["name"], *temple.get("aliases", [])]

    def display_name(self, temple_id: str) -> str:
        temple = self.meta.get(temple_id) or {}
        return temple.get("name") or temple_id

    def resolve(self, query: str):
        exact = self._resolve_exact(query)
        if exact:
            return exact
        return self._resolve_fuzzy(query)

    def _from_matches(self, matches):
        if not matches:
            return None

        matches.sort(key=lambda x: len(x[0]), reverse=True)
        best_len = len(matches[0][0])
        top_ids = []
        for alias, temple_id in matches:
            if len(alias) != best_len:
                continue
            if temple_id not in top_ids:
                top_ids.append(temple_id)

        if len(top_ids) > 1:
            return {
                "temple_id": None,
                "matched_name": matches[0][0],
                "confidence": 0.0,
                "ambiguous": True,
                "candidates": [
                    {
                        "temple_id": temple_id,
                        "name": self.display_name(temple_id),
                    }
                    for temple_id in top_ids
                ],
            }

        return {
            "temple_id": top_ids[0],
            "matched_name": matches[0][0],
            "confidence": 1.0,
            "ambiguous": False,
            "candidates": [],
        }

    def _resolve_exact(self, query: str):
        normalized_query = normalize(query)
        matches = []

        for alias, temple_ids in self.alias_map.items():
            pattern = r"\b" + re.escape(alias) + r"\b"
            if re.search(pattern, normalized_query):
                for temple_id in temple_ids:
                    matches.append((alias, temple_id))

        return self._from_matches(matches)

    def _resolve_fuzzy(self, query: str):
        normalized_query = normalize(query)
        if not normalized_query:
            return None

        scored = []
        q_compact = compact(normalized_query)

        for alias, temple_ids in self.alias_map.items():
            if len(alias) < FUZZY_MIN_ALIAS:
                continue

            a_compact = compact(alias)
            scores = [
                SequenceMatcher(None, alias, normalized_query).ratio(),
                SequenceMatcher(None, a_compact, q_compact).ratio(),
            ]

            for token in normalized_query.split():
                if len(token) < 5:
                    continue
                scores.append(SequenceMatcher(None, alias, token).ratio())
                scores.append(SequenceMatcher(None, a_compact, compact(token)).ratio())

            score = max(scores)
            if score >= FUZZY_THRESHOLD:
                for temple_id in temple_ids:
                    scored.append((score, alias, temple_id))

        if not scored:
            return None

        scored.sort(key=lambda x: x[0], reverse=True)
        best = scored[0][0]
        top_ids = []
        matched = scored[0][1]
        for score, alias, temple_id in scored:
            if best - score > 0.03:
                break
            if temple_id not in top_ids:
                top_ids.append(temple_id)

        if len(top_ids) > 1:
            return {
                "temple_id": None,
                "matched_name": matched,
                "confidence": best,
                "ambiguous": True,
                "candidates": [
                    {
                        "temple_id": temple_id,
                        "name": self.display_name(temple_id),
                    }
                    for temple_id in top_ids
                ],
            }

        return {
            "temple_id": top_ids[0],
            "matched_name": matched,
            "confidence": best,
            "ambiguous": False,
            "candidates": [],
        }
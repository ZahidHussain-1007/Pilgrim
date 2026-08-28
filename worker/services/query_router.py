import re
from difflib import SequenceMatcher

from temple_resolver import TempleResolver, normalize


CLARIFY_TEMPLE = (
    "Which temple are you asking about? "
    "For example: Yadadri, Bhadrachalam, Ramappa, Medaram, or Sanghi."
)

EDGE_WORDS = {
    "of", "at", "in", "for", "about", "from", "to",
    "the", "a", "an", "please", "temple",
    "it", "this", "that", "there", "here", "its",
}

FILLER_WORDS = {
    "tell", "me", "please", "can", "you", "could",
    "i", "want", "know", "something", "info",
    "information", "details",
}

OVERVIEW_QUERIES = [
    "temple overview",
    "history and religious significance",
    "location address how to reach",
    "darshan timings",
    "dress code and facilities",
]

EMERGENCY_CUES = {
    "hospital", "hospitals", "ambulance", "emergency",
    "police", "pharmacy", "medical", "doctor", "clinic",
    "phc",
}

HOTEL_CUES = {
    "hotel", "hotels", "stay", "staying", "accommodation",
    "lodge", "lodges", "room", "rooms", "guest",
    "guesthouse", "cottage", "cottages",
    "hostel", "hostels", "dharmashala", "dharamshala",
}

FOOD_CUES = {
    "food", "restaurant", "restaurants", "eat", "eating",
    "breakfast", "lunch", "dinner", "meals", "annadanam",
    "tiffin",
}

SPELLINGS = [
    (r"\bdashan\b", "darshan"),
    (r"\bdarsan\b", "darshan"),
    (r"\bdharshan\b", "darshan"),
    (r"\bsevaas\b", "sevas"),
]

SECTION_RULES = [
    (
        ["darshan", "timing", "timings", "open", "close", "hours", "schedule"],
        ["darshan_timings", "faq_FAQ004", "darshan_and_tickets"],
    ),
    (
        ["seva", "sevas", "pooja", "poojas", "archana", "abhishekam"],
        ["sevas", "rituals", "special_poojas"],
    ),
    (
        ["where", "address", "location", "reach", "route", "routes",
         "bus", "buses", "train", "airport", "travel"],
        ["travel", "contact"],
    ),
    (
        ["dress", "wear", "clothing"],
        ["dress_code"],
    ),
    (
        ["nearby", "attraction", "attractions", "places", "sightseeing"],
        ["nearby_places"],
    ),
    (
        ["hospital", "hospitals", "doctor", "clinic", "phc"],
        ["hospital"],
    ),
    (
        ["police"],
        ["police"],
    ),
    (
        ["pharmacy", "medical"],
        ["pharmacy"],
    ),
]

INTENT_VOCAB = sorted(
    EMERGENCY_CUES
    | HOTEL_CUES
    | FOOD_CUES
    | {
        "darshan", "timings", "timing", "hours", "schedule",
        "seva", "sevas", "pooja", "poojas",
        "travel", "route", "routes", "bus", "buses",
        "train", "airport", "address", "location", "reach",
        "dress", "nearby", "attraction", "attractions",
        "hospital", "hotels", "food",
    }
)


def fix_spellings(text: str) -> str:
    out = text
    for pattern, repl in SPELLINGS:
        out = re.sub(pattern, repl, out)
    return out


def fuzzy_intent_query(query: str) -> str:
    tokens = normalize(fix_spellings(query.lower())).split()
    fixed = []
    for token in tokens:
        if len(token) < 3 or token in INTENT_VOCAB:
            fixed.append(token)
            continue
        best_word = token
        best_score = 0.0
        for word in INTENT_VOCAB:
            if abs(len(word) - len(token)) > 3:
                continue
            score = SequenceMatcher(None, token, word).ratio()
            if score > best_score:
                best_score = score
                best_word = word
        fixed.append(best_word if best_score >= 0.78 else token)
    return " ".join(fixed)


def _usable(text: str) -> bool:
    return bool(re.search(r"[a-z0-9]{3,}", text))


def _has_cue(text: str, cues: set) -> bool:
    return any(re.search(r"\b" + re.escape(cue) + r"\b", text) for cue in cues)


def detect_entity(query: str) -> str:
    text = normalize(query)
    if _has_cue(text, EMERGENCY_CUES):
        return "emergency"
    if _has_cue(text, HOTEL_CUES):
        return "hotel"
    if _has_cue(text, FOOD_CUES):
        return "restaurant"
    return "temple"


def preferred_sections(query: str, entity: str) -> list:
    text = normalize(query)
    if entity == "hotel":
        return ["hotel"]
    if entity == "restaurant":
        return ["restaurant"]
    for cues, sections in SECTION_RULES:
        if any(re.search(r"\b" + re.escape(cue) + r"\b", text) for cue in cues):
            return sections
    return []


def build_slot_query(query: str, alias_names: list) -> str:
    text = normalize(query)

    for name in sorted((normalize(n) for n in alias_names), key=len, reverse=True):
        if not name:
            continue
        text = re.sub(r"\b" + re.escape(name) + r"\b", " ", text)

    text = re.sub(r"\s+", " ", text).strip()
    tokens = text.split()

    while tokens and tokens[0] in EDGE_WORDS:
        tokens.pop(0)
    while tokens and tokens[-1] in EDGE_WORDS:
        tokens.pop()

    return " ".join(tokens)


def is_overview_intent(slot_query: str, entity: str) -> bool:
    if entity != "temple":
        return False
    if not _usable(slot_query):
        return True
    content = [
        tok for tok in slot_query.split()
        if tok not in FILLER_WORDS and tok not in EDGE_WORDS
    ]
    return len(content) == 0


def _blocked(query: str, entity: str) -> dict:
    return {
        "status": "needs_temple",
        "intent": "needs_temple",
        "entity": entity,
        "temple_id": None,
        "matched_name": None,
        "confidence": 0.0,
        "query": query,
        "retrieval_query": None,
        "retrieval_queries": [],
        "preferred_sections": [],
        "should_retrieve": False,
        "message": CLARIFY_TEMPLE,
    }


class QueryRouter:

    def __init__(self, resolver=None):
        self.resolver = resolver or TempleResolver()

    def _filled_slot(self, entity: str, slot_query: str) -> str:
        if _usable(slot_query):
            return slot_query
        
        slot_query = self._filled_slot(entity, slot_query)

        if entity == "hotel":
            slot_query = "hotels accommodation lodge hostel guest house stay"
        elif entity == "restaurant":
            slot_query = "restaurants food meals tiffin"
        elif entity == "emergency":
            slot_query = "hospital ambulance police pharmacy"

        return {
            "status": "resolved",
            "intent": "slot",
            "entity": entity,
            "temple_id": resolved["temple_id"],
            "matched_name": resolved["matched_name"],
            "confidence": resolved.get("confidence", 1.0),
            "query": query,
            "retrieval_query": slot_query,
            "retrieval_queries": [slot_query],
            "preferred_sections": sections,
            "should_retrieve": True,
            "message": None,
        }
        return "temple overview"

    def _decision(self, query, entity, resolved):
        aliases = self.resolver.aliases_for(resolved["temple_id"])
        slot_query = build_slot_query(query, aliases)
        sections = preferred_sections(query, entity)

        if is_overview_intent(slot_query, entity):
            return {
                "status": "resolved",
                "intent": "overview",
                "entity": entity,
                "temple_id": resolved["temple_id"],
                "matched_name": resolved["matched_name"],
                "confidence": resolved.get("confidence", 1.0),
                "query": query,
                "retrieval_query": OVERVIEW_QUERIES[0],
                "retrieval_queries": list(OVERVIEW_QUERIES),
                "preferred_sections": sections,
                "should_retrieve": True,
                "message": None,
            }

        slot_query = self._filled_slot(entity, slot_query)
        return {
            "status": "resolved",
            "intent": "slot",
            "entity": entity,
            "temple_id": resolved["temple_id"],
            "matched_name": resolved["matched_name"],
            "confidence": resolved.get("confidence", 1.0),
            "query": query,
            "retrieval_query": slot_query,
            "retrieval_queries": [slot_query],
            "preferred_sections": sections,
            "should_retrieve": True,
            "message": None,
        }

    def route_with_temple(self, query: str, temple_id: str) -> dict:
        routed = fuzzy_intent_query(query)
        entity = detect_entity(routed)
        resolved = {
            "temple_id": temple_id,
            "matched_name": self.resolver.display_name(temple_id),
            "confidence": 1.0,
        }
        return self._decision(routed, entity, resolved)

    def route(self, query: str) -> dict:
        query = (query or "").strip()
        if not query:
            return _blocked(query, "temple")

        resolved = self.resolver.resolve(query)
        routed = fuzzy_intent_query(query)
        entity = detect_entity(routed)

        if resolved is None:
            return _blocked(query, entity)

        if resolved.get("ambiguous"):
            names = ", ".join(
                f"{item['name']} ({item['temple_id']})"
                for item in resolved["candidates"]
            )
            return {
                "status": "ambiguous",
                "intent": "needs_temple",
                "entity": entity,
                "temple_id": None,
                "matched_name": resolved.get("matched_name"),
                "confidence": 0.0,
                "query": query,
                "retrieval_query": None,
                "retrieval_queries": [],
                "preferred_sections": [],
                "should_retrieve": False,
                "message": f"Which temple do you mean: {names}?",
            }

        return self._decision(routed, entity, resolved)
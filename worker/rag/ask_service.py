import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "rag"))
sys.path.insert(0, str(ROOT / "services"))

from query_router import QueryRouter
from retrieve import retrieve
from context_builder import build_context
from gemini_generator import generate_answer
from temple_resolver import normalize
from travel_intent import is_route_query, extract_travel_slots, compare_kind
from travel_intent import parse_mode as intent_parse_mode
from travel_bridge import plan_to_temple, resolve_origin, compare_to_temple, format_compare, drive_km_to_temple
from travel_timing import darshan_travel_advice
from travel_pins import catalog_pins, format_pins, is_on_way_followup, wants_route_pins
from budget import (
    is_budget_query,
    plan_budget,
    format_budget,
    parse_slot_patch,
    query_for_temple,
    merge_form,
    resolve_trip_km,
    load_catalog_slice,
    origin_matches_plan,
)


def parse_mode(query: str):
    return intent_parse_mode(query)


router = QueryRouter()

YES = {
    "yes", "y", "yeah", "yep", "ok", "okay", "sure",
    "ji", "ha", "haan", "please", "do it",
}

NO = {"no", "n", "nope", "nah"}

CLARIFY = [
    {
        "triggers": ["hostel", "hostels", "dharmashala", "dharamshala"],
        "entity": "hotel",
        "canonical": "hotels",
        "label": "hotels or lodges",
    },
    {
        "triggers": ["tiffin", "canteen", "dhaba"],
        "entity": "restaurant",
        "canonical": "restaurants",
        "label": "restaurants or food",
    },
    {
        "triggers": ["doctor", "clinic", "phc"],
        "entity": "emergency",
        "canonical": "hospitals",
        "label": "hospitals or medical help",
    },
]


def _has_word(text, word):
    return bool(re.search(r"\b" + re.escape(word) + r"\b", text))


def _clarify_rule(query):
    text = normalize(query)
    for rule in CLARIFY:
        hit = next((t for t in rule["triggers"] if _has_word(text, t)), None)
        if not hit:
            continue
        if _has_word(text, rule["canonical"]) or _has_word(text, rule["canonical"][:-1]):
            return None
        return {**rule, "trigger": hit}
    return None


def _pack(decision, results, answer):
    sources = []
    seen = set()
    for item in results or []:
        payload = item["payload"]
        meta = payload.get("metadata") or {}
        name = (
            meta.get("hotel_name")
            or meta.get("restaurant_name")
            or payload.get("section")
        )
        key = (
            payload.get("entity_type"),
            payload.get("entity_id") or name,
        )
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            {
                "temple_id": payload.get("temple_id"),
                "entity_type": payload.get("entity_type"),
                "section": payload.get("section"),
                "chunk_id": payload.get("chunk_id"),
                "name": name,
            }
        )
    return {
        "status": "ok" if decision.get("should_retrieve") else decision["status"],
        "entity": decision.get("entity"),
        "temple_id": decision.get("temple_id"),
        "intent": decision.get("intent"),
        "answer": answer,
        "sources": sources,
    }


def _run(decision, user_query):
    if not decision.get("should_retrieve"):
        return {
            "status": decision["status"],
            "entity": decision.get("entity"),
            "temple_id": decision.get("temple_id"),
            "intent": decision.get("intent"),
            "answer": decision.get("message"),
            "sources": [],
        }
    results = retrieve(decision, verbose=False)
    max_chunks = 8 if decision.get("intent") == "overview" else 5
    context = build_context(results, max_chunks=max_chunks)
    answer = generate_answer(user_query, context)
    return _pack(decision, results[:max_chunks], answer)


def _parse_source(query):
    try:
        from travel.agents.intent_agent import IntentAgent

        parsed = IntentAgent().parse(query)
        if parsed.source and parsed.source.lower() != "unknown":
            return parsed.source
    except Exception:
        return None
    return None


def _format_travel(result):
    if result.get("status") == "needs_origin":
        return result.get("question") or "From which city or station?"
    if result.get("status") == "unknown_temple":
        return result.get("question") or "Which temple?"

    lines = []
    name = result.get("temple_name") or result.get("temple_id")
    source = result.get("source") or ""
    used = result.get("origin_used") or source
    lines.append(f"Travel to {name} from {source}.")
    if used and used != source:
        lines.append(f"I used: {used}")
        lines.append("If that start is wrong, say the full area name (e.g. Peerzadiguda Khaman, Hyderabad).")

    if result.get("recommendation"):
        lines.append(f"Suggestion: {result['recommendation']}")

    options = result.get("options") or []
    if options:
        lines.append("")
        for i, option in enumerate(options[:4], 1):
            dur = option.get("duration_minutes")
            km = option.get("distance_km") or 0
            hint = (option.get("mode_hint") or "route").lower()
            if hint == "car":
                tail = f"{km:.1f} km"
            elif hint == "train":
                tail = f"{option.get('transfers', 0)} change(s), {km:.1f} km"
            else:
                tail = f"{option.get('transfers', 0)} bus change(s), {km:.1f} km"
            if dur is not None:
                tail += f", {dur} min"
            src = option.get("live_source") or ""
            lines.append(f"WAY {i} — {option.get('mode_hint', 'route').upper()} — {tail}")
            if src:
                lines.append(f"   ({src})")
            steps = option.get("steps") or []
            if steps:
                for n, step in enumerate(steps, 1):
                    lines.append(f"   {n}. {step}")
            elif option.get("via"):
                lines.append("   Via: " + " → ".join(option["via"]))
            if option.get("note"):
                lines.append(f"   Note: {option['note']}")
    elif result.get("route"):
        route = result["route"]
        lines.append(route.get("summary") or "")
        if route.get("via"):
            lines.append("Via: " + " → ".join(route["via"]))
    else:
        lines.append("Google Maps did not return a live path. I will not invent a bus or train.")
        lines.append("Use the nearest bus / railway from our temple file, or try again in a minute.")

    facts = result.get("corpus_travel") or {}
    if facts.get("nearest_railway"):
        lines.append(f"Nearest railway: {facts['nearest_railway']}")
    if facts.get("nearest_bus"):
        lines.append(f"Nearest bus: {facts['nearest_bus']}")

    on_way = result.get("attractions_on_way") or []
    at_end = result.get("attractions_at_temple") or result.get("attractions") or []
    if on_way:
        lines.append("On this way: " + "; ".join(str(x) for x in on_way[:5]))
    else:
        lines.append("On this way: none on this bus/car path.")
    if at_end:
        names = [a.get("name") if isinstance(a, dict) else str(a) for a in at_end[:5]]
        lines.append("At the temple: " + "; ".join(names))
    if result.get("darshan_advice"):
        lines.append(result["darshan_advice"])
    for extra in result.get("pin_lines") or []:
        lines.append(extra)

    return "\n".join(lines)


def _run_travel(temple_id, source, session, mode="transit", query=""):
    try:
        result = plan_to_temple(temple_id, source=source, mode=mode)
    except Exception:
        result = {
            "status": "no_route",
            "temple_id": temple_id,
            "temple_name": temple_id,
            "source": source,
            "mode": mode,
            "options": [],
            "warnings": ["Google Maps failed. I will not invent a route."],
            "corpus_travel": {},
        }
    duration = None
    if result.get("options"):
        duration = result["options"][0].get("duration_minutes")
    if duration is None and result.get("route"):
        duration = result["route"].get("duration_minutes")
    stored = session.get("travel_query") or query
    advice = darshan_travel_advice(temple_id, duration, stored)
    if advice:
        result["darshan_advice"] = advice
    session["last_travel"] = {
        "temple_id": temple_id,
        "option": (result.get("options") or [None])[0],
        "source": source,
        "mode": mode,
    }
    session["last_travel_plan"] = result
    answer = _format_travel(result)
    return {
        "status": "ok" if result.get("status") in {"ok", "no_route"} else result.get("status"),
        "entity": "travel",
        "temple_id": temple_id,
        "intent": "route",
        "answer": answer,
        "sources": [
            {
                "temple_id": temple_id,
                "entity_type": "travel",
                "section": "route",
                "chunk_id": None,
                "name": "travel_engine",
            }
        ],
    }, session


def _run_compare(temple_id, source, session, kind, query=""):
    result = compare_to_temple(temple_id, source, kind=kind or "compare")
    session["last_travel"] = {
        "temple_id": temple_id,
        "option": ((result.get("rows") or [{}])[0].get("option") if result.get("rows") else None),
        "source": source,
        "mode": "compare",
    }
    session["last_travel_plan"] = result
    session["travel_query"] = query or session.get("travel_query") or ""
    return {
        "status": "ok" if result.get("status") in {"ok", "no_route"} else result.get("status"),
        "entity": "travel",
        "temple_id": temple_id,
        "intent": "compare",
        "answer": format_compare(result),
        "sources": [
            {
                "temple_id": temple_id,
                "entity_type": "travel",
                "section": "compare",
                "chunk_id": None,
                "name": "travel_engine",
            }
        ],
    }, session


def _run_budget(query, session):
    previous = session.get("temple_id")
    decision, session = _resolve_temple(query_for_temple(query), session)
    if decision.get("status") == "ambiguous":
        return {
            "status": "ambiguous",
            "entity": "budget",
            "temple_id": None,
            "intent": "budget",
            "answer": decision.get("message"),
            "sources": [],
        }, session
    temple_id = decision.get("temple_id") or session.get("temple_id")
    if not temple_id:
        return {
            "status": "needs_temple",
            "entity": "budget",
            "temple_id": None,
            "intent": "budget",
            "answer": "Which temple is this budget for?",
            "sources": [],
        }, session
    if previous and temple_id != previous:
        session.pop("last_travel_plan", None)
        session.pop("last_travel", None)
        session.pop("pending_travel_origin", None)
        session.pop("pending_travel_mode", None)
        session.pop("budget_form", None)

    form = dict(session.get("budget_form") or {})
    form["temple_id"] = temple_id
    merged = merge_form(form, query)
    people = merged.get("people")
    days = merged.get("days")
    nights = merged.get("nights")
    rooms = merged.get("rooms") or 0
    origin = merged.get("origin")
    round_trip = bool(merged.get("round_trip"))
    car_seats = merged.get("car_seats")
    asked = parse_mode(query)
    travel_mode = merged.get("travel_mode")
    if asked in {"transit", "bus"}:
        travel_mode = "bus"
    elif asked in {"drive", "car"}:
        travel_mode = "car"
    elif asked == "train":
        travel_mode = "train"

    catalog = load_catalog_slice(str(temple_id))
    last_plan = session.get("last_travel_plan")
    plan_ok = bool(
        last_plan
        and last_plan.get("temple_id") == temple_id
        and origin_matches_plan(origin, last_plan)
    )
    route = resolve_trip_km(
        origin=origin,
        temple_id=temple_id,
        hyd_km=catalog.get("road_km"),
        travel_plan=last_plan if plan_ok else None,
        cached_km=merged.get("distance_km") if merged.get("origin") == form.get("origin") else None,
        cached_origin=form.get("origin"),
        cached_source=form.get("km_source"),
        cached_lookup=form.get("km_lookup"),
        drive_km_fn=drive_km_to_temple,
    )
    travel = {}
    if route.get("distance_km") is not None:
        travel["distance_km"] = route["distance_km"]
    if travel_mode:
        travel["mode_asked"] = travel_mode

    card = plan_budget(
        {
            "temple_id": temple_id,
            "query": query,
            "origin": origin,
            "round_trip": round_trip,
            "people": people,
            "days": days,
            "nights": nights,
            "rooms": rooms,
            "car_seats": car_seats,
            "passenger_capacity": merged.get("passenger_capacity"),
            "driver_included": merged.get("driver_included"),
            "selected_sevas": merged.get("selected_sevas") or [],
            "budget": session.get("budget_limit"),
            "catalog": catalog,
            "travel": travel,
            "travel_plan": last_plan if route.get("travel_plan_ok") else None,
            "travel_mode": travel_mode,
            "km_source": route.get("km_source"),
        }
    )
    inp = card.get("input") or {}
    km_lookup = "ok" if inp.get("has_km") else ("miss" if origin else form.get("km_lookup"))
    session["budget_form"] = {
        "temple_id": temple_id,
        "people": inp.get("people"),
        "days": inp.get("days"),
        "nights": inp.get("nights"),
        "rooms": rooms,
        "origin": inp.get("origin") or origin,
        "round_trip": inp.get("round_trip"),
        "car_seats": inp.get("car_seats"),
        "passenger_capacity": inp.get("passenger_seats"),
        "driver_included": inp.get("driver_included"),
        "travel_mode": travel_mode,
        "selected_sevas": list(inp.get("selected_sevas") or []),
        "distance_km": inp.get("distance_km"),
        "km_source": inp.get("km_source"),
        "km_lookup": km_lookup,
        "duration_minutes": route.get("duration_minutes"),
    }
    return {
        "status": "ok",
        "entity": "budget",
        "temple_id": temple_id,
        "intent": "budget",
        "answer": format_budget(card),
        "sources": [
            {
                "temple_id": temple_id,
                "entity_type": "budget",
                "section": "catalog",
                "chunk_id": None,
                "name": "budget_engine",
            }
        ],
    }, session


def _resolve_temple(query, session):
    decision = router.route(query)
    if decision.get("status") == "resolved":
        session["temple_id"] = decision["temple_id"]
        session["temple_name"] = router.resolver.display_name(decision["temple_id"])
    elif decision.get("status") == "needs_temple" and session.get("temple_id"):
        decision = router.route_with_temple(query, session["temple_id"])
    return decision, session


def ask(query: str, session=None):
    session = dict(session or {})
    text = normalize(query)

    pending = session.get("pending_clarify")
    if pending:
        if text in NO:
            session.pop("pending_clarify", None)
            return {
                "status": "ok",
                "entity": pending["entity"],
                "temple_id": session.get("temple_id"),
                "intent": "slot",
                "answer": "Okay. Ask another question when you want.",
                "sources": [],
            }, session

        if text in YES or pending["canonical"] in text or pending["entity"] in text:
            session.pop("pending_clarify", None)
            temple_id = session.get("temple_id")
            if not temple_id:
                return {
                    "status": "needs_temple",
                    "entity": pending["entity"],
                    "temple_id": None,
                    "intent": "needs_temple",
                    "answer": "Which temple are you asking about?",
                    "sources": [],
                }, session
            decision = router.route_with_temple(pending["canonical"], temple_id)
            return _run(decision, pending["canonical"]), session

        session.pop("pending_clarify", None)

    pending_mode = session.get("pending_travel_mode")
    if pending_mode:
        if text in NO:
            session.pop("pending_travel_mode", None)
            return {
                "status": "ok",
                "entity": "travel",
                "temple_id": pending_mode.get("temple_id"),
                "intent": "route",
                "answer": "Okay. Ask another question when you want.",
                "sources": [],
            }, session
        slots = extract_travel_slots(query)
        kind = slots.get("compare") or compare_kind(query)
        # A new full sentence replaces the old start city (Narayanaguda bug).
        if is_route_query(query) and slots.get("source"):
            session.pop("pending_travel_mode", None)
            source = slots["source"]
            if kind:
                return _run_compare(pending_mode["temple_id"], source, session, kind, query=query)
            if slots.get("mode"):
                return _run_travel(pending_mode["temple_id"], source, session, mode=slots["mode"], query=query)
            session["pending_travel_mode"] = {
                "temple_id": pending_mode["temple_id"],
                "source": source,
                "query": query,
            }
            return {
                "status": "needs_mode",
                "entity": "travel",
                "temple_id": pending_mode["temple_id"],
                "intent": "route",
                "answer": "How do you want to go? Reply bus, train, or car. Or say cheapest / fastest / longest.",
                "sources": [],
            }, session
        if kind:
            session.pop("pending_travel_mode", None)
            return _run_compare(
                pending_mode["temple_id"],
                pending_mode["source"],
                session,
                kind,
                query=query,
            )
        chosen = parse_mode(query)
        if not chosen:
            if len((query or "").split()) >= 2 or len(query or "") > 8:
                from travel_bridge import resolve_origin

                origin = resolve_origin(query.strip())
                pending_mode["source"] = origin["label"] or query.strip()
                session["pending_travel_mode"] = pending_mode
                return {
                    "status": "needs_mode",
                    "entity": "travel",
                    "temple_id": pending_mode.get("temple_id"),
                    "intent": "route",
                    "answer": (
                        f"I used: {pending_mode['source']}. "
                        "How do you want to go? Reply bus, train, or car. Or say cheapest / fastest / longest."
                    ),
                    "sources": [],
                }, session
            return {
                "status": "needs_mode",
                "entity": "travel",
                "temple_id": pending_mode.get("temple_id"),
                "intent": "route",
                "answer": "Please reply with bus, train, or car. Or say cheapest / fastest / longest.",
                "sources": [],
            }, session
        session.pop("pending_travel_mode", None)
        return _run_travel(pending_mode["temple_id"], pending_mode["source"], session, mode=chosen)

    pending_origin = session.get("pending_travel_origin")
    if pending_origin and not is_route_query(query):
        if text in NO:
            session.pop("pending_travel_origin", None)
            return {
                "status": "ok",
                "entity": "travel",
                "temple_id": pending_origin.get("temple_id"),
                "intent": "route",
                "answer": "Okay. Ask another question when you want.",
                "sources": [],
            }, session
        if parse_mode(query) and len(query.split()) <= 2:
            return {
                "status": "needs_origin",
                "entity": "travel",
                "temple_id": pending_origin.get("temple_id"),
                "intent": "route",
                "answer": "First tell me the starting city or station. Then I will ask bus, train, or car.",
                "sources": [],
            }, session
        session.pop("pending_travel_origin", None)
        session["pending_travel_mode"] = {
            "temple_id": pending_origin["temple_id"],
            "source": query.strip(),
            "query": pending_origin.get("query") or session.get("travel_query") or "",
        }
        return {
            "status": "needs_mode",
            "entity": "travel",
            "temple_id": pending_origin["temple_id"],
            "intent": "route",
            "answer": "How do you want to go? Reply bus, train, or car.",
            "sources": [],
        }, session

    if pending_origin and is_route_query(query):
        session.pop("pending_travel_origin", None)

    last_trip = session.get("last_travel")
    if is_budget_query(query):
        return _run_budget(query, session)

    if last_trip and is_on_way_followup(query) and not is_route_query(query):
        hotels = catalog_pins(last_trip["temple_id"], last_trip.get("option"), "hotel")
        food = catalog_pins(last_trip["temple_id"], last_trip.get("option"), "restaurant")
        return {
            "status": "ok",
            "entity": "travel",
            "temple_id": last_trip["temple_id"],
            "intent": "route_pins",
            "answer": "\n".join(format_pins(hotels, food)),
            "sources": [
                {
                    "temple_id": last_trip["temple_id"],
                    "entity_type": "travel",
                    "section": "pins",
                    "chunk_id": None,
                    "name": "catalog",
                }
            ],
        }, session

    if is_route_query(query):
        decision, session = _resolve_temple(query, session)
        if decision.get("status") == "ambiguous":
            return {
                "status": "ambiguous",
                "entity": "travel",
                "temple_id": None,
                "intent": "route",
                "answer": decision.get("message"),
                "sources": [],
            }, session

        temple_id = decision.get("temple_id") or session.get("temple_id")
        if not temple_id:
            return {
                "status": "needs_temple",
                "entity": "travel",
                "temple_id": None,
                "intent": "route",
                "answer": "Which temple are you travelling to?",
                "sources": [],
            }, session

        slots = extract_travel_slots(query)
        if not temple_id and slots.get("destination"):
            extra, session = _resolve_temple(slots["destination"], session)
            temple_id = extra.get("temple_id") or session.get("temple_id") or temple_id
        if not temple_id:
            return {
                "status": "needs_temple",
                "entity": "travel",
                "temple_id": None,
                "intent": "route",
                "answer": "Which temple are you travelling to?",
                "sources": [],
            }, session

        source = slots.get("source") or _parse_source(query)
        mode = slots.get("mode") or parse_mode(query)
        kind = slots.get("compare") or compare_kind(query)
        session["travel_query"] = query
        if not source:
            session["pending_travel_origin"] = {"temple_id": temple_id, "query": query}
            return {
                "status": "needs_origin",
                "entity": "travel",
                "temple_id": temple_id,
                "intent": "route",
                "answer": "From which city or station?",
                "sources": [],
            }, session

        if kind:
            return _run_compare(temple_id, source, session, kind, query=query)

        if not mode:
            session["pending_travel_mode"] = {
                "temple_id": temple_id,
                "source": source,
                "query": query,
            }
            return {
                "status": "needs_mode",
                "entity": "travel",
                "temple_id": temple_id,
                "intent": "route",
                "answer": "How do you want to go? Reply bus, train, or car. Or say cheapest / fastest / longest.",
                "sources": [],
            }, session

        return _run_travel(temple_id, source, session, mode=mode, query=query)

    # Same trip form: "7 seater" / "3 rooms" patches fields and re-runs. Not Groq.
    if session.get("budget_form") and not is_route_query(query) and not is_budget_query(query):
        if parse_slot_patch(query):
            return _run_budget(query, session)

    # Rupees / fare / afford — budget room. Not Groq. Travel already handled routes.
    if is_budget_query(query):
        return _run_budget(query, session)

    decision = router.route(query)

    if decision.get("status") == "resolved":
        session["temple_id"] = decision["temple_id"]
        session["temple_name"] = router.resolver.display_name(decision["temple_id"])

    elif decision.get("status") == "needs_temple" and session.get("temple_id"):
        decision = router.route_with_temple(query, session["temple_id"])

    elif decision.get("status") == "ambiguous":
        return {
            "status": "ambiguous",
            "entity": decision.get("entity"),
            "temple_id": None,
            "intent": "needs_temple",
            "answer": decision.get("message"),
            "sources": [],
        }, session

    rule = _clarify_rule(query)
    if rule and decision.get("should_retrieve") and decision.get("entity") == rule["entity"]:
        temple_name = session.get("temple_name") or "this temple"
        session["pending_clarify"] = rule
        return {
            "status": "clarify",
            "entity": rule["entity"],
            "temple_id": decision.get("temple_id"),
            "intent": "slot",
            "answer": (
                f"I don't have {rule['trigger']} listed for {temple_name}. "
                f"Do you mean {rule['label']}?"
            ),
            "sources": [],
        }, session

    if not decision.get("should_retrieve"):
        return {
            "status": decision["status"],
            "entity": decision.get("entity"),
            "temple_id": decision.get("temple_id"),
            "intent": decision.get("intent"),
            "answer": decision.get("message"),
            "sources": [],
        }, session

    return _run(decision, query), session

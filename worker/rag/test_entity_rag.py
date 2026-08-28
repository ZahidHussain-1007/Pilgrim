import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "services"))

from query_router import QueryRouter
from retrieve import retrieve
from context_builder import build_context
from gemini_generator import generate_answer


router = QueryRouter()


def answer_query(query):
    decision = router.route(query)
    print("=" * 80)
    print("USER QUERY :", query)
    print("STATUS     :", decision["status"])
    print("ENTITY     :", decision.get("entity"))
    print("TEMPLE ID  :", decision["temple_id"])
    print("=" * 80)

    if not decision["should_retrieve"]:
        return decision, None, decision["message"], False

    results = retrieve(decision, verbose=False)
    context = build_context(results, max_chunks=5)
    answer = generate_answer(query, context)
    return decision, results, answer, True


def payload_set(results, key):
    return {item["payload"].get(key) for item in (results or [])}


def main():
    passed = 0

    hotel_q = "Hotels near Yadadri"
    decision, results, answer, called = answer_query(hotel_q)
    ok = (
        decision.get("entity") == "hotel"
        and decision["temple_id"] == "T0001"
        and called
        and payload_set(results, "entity_type") == {"hotel"}
        and payload_set(results, "temple_id") == {"T0001"}
        and ("hotel" in answer.lower() or "stay" in answer.lower() or "room" in answer.lower())
    )
    passed += int(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] hotel Gemini")
    print(answer)
    print()

    sos_q = "Nearest hospital to Yadadri"
    decision, results, answer, called = answer_query(sos_q)
    sections = [item["payload"].get("section") for item in (results or [])]
    ok = (
        decision.get("entity") == "emergency"
        and decision["temple_id"] == "T0001"
        and called
        and payload_set(results, "entity_type") == {"emergency"}
        and "hospital" in sections
        and ("hospital" in answer.lower() or "thirumalamma" in answer.lower())
    )
    passed += int(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] hospital Gemini")
    print(answer)

    print("=" * 80)
    print(f"RESULT: {passed}/2")
    print("=" * 80)
    if passed != 2:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
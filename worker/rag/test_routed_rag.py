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
    print(f"USER QUERY : {query}")
    print(f"STATUS     : {decision['status']}")
    print(f"INTENT     : {decision.get('intent')}")
    print(f"TEMPLE ID  : {decision['temple_id']}")
    print(f"QUERIES    : {decision.get('retrieval_queries')}")
    print("=" * 80)

    if not decision["should_retrieve"]:
        return {
            "decision": decision,
            "results": None,
            "answer": decision["message"],
            "called_retrieve": False,
            "called_gemini": False,
        }

    results = retrieve(decision, verbose=False)
    max_chunks = 8 if decision.get("intent") == "overview" else 5
    context = build_context(results, max_chunks=max_chunks)
    answer = generate_answer(query, context)

    return {
        "decision": decision,
        "results": results,
        "answer": answer,
        "called_retrieve": True,
        "called_gemini": True,
    }


def sections_of(results):
    return [item["payload"].get("section") for item in (results or [])]


def main():
    passed = 0

    unnamed = answer_query("What are the darshan timings?")
    ok = (
        unnamed["called_retrieve"] is False
        and unnamed["called_gemini"] is False
        and "Which temple" in unnamed["answer"]
    )
    passed += int(ok)
    print(f"\n[{'PASS' if ok else 'FAIL'}] unnamed query does not call Gemini")
    print(f"ANSWER:\n{unnamed['answer']}\n")

    slot = answer_query("What are the darshan timings of Yadadri?")
    slot_sections = sections_of(slot["results"])
    slot_text = (slot["answer"] or "").lower()
    ok = (
        slot["decision"]["intent"] == "slot"
        and slot["decision"]["temple_id"] == "T0001"
        and slot["called_gemini"] is True
        and "darshan_timings" in slot_sections
        and ("6:00" in slot["answer"] or "6:00 am" in slot_text or "6 am" in slot_text)
    )
    passed += int(ok)
    print(f"\n[{'PASS' if ok else 'FAIL'}] Yadadri timings stay a slot")
    print(f"SECTIONS: {slot_sections}")
    print("\nPILGRIMAI ANSWER")
    print("-" * 80)
    print(slot["answer"])

    overview = answer_query("Tell me about Yadadri")
    overview_sections = sections_of(overview["results"])
    overview_text = (overview["answer"] or "").lower()
    ok = (
        overview["decision"]["intent"] == "overview"
        and overview["decision"]["temple_id"] == "T0001"
        and overview["called_gemini"] is True
        and "darshan_timings" in overview_sections
        and ("history" in overview_sections or "overview" in overview_sections)
        and ("narasimha" in overview_text or "yadadri" in overview_text)
        and ("6:00" in overview["answer"] or "darshan" in overview_text)
    )
    passed += int(ok)
    print(f"\n[{'PASS' if ok else 'FAIL'}] Yadadri overview briefing")
    print(f"SECTIONS: {overview_sections}")
    print("\nPILGRIMAI ANSWER")
    print("-" * 80)
    print(overview["answer"])

    print("\n" + "=" * 80)
    print(f"RESULT: {passed}/3")
    print("=" * 80)
    if passed != 3:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
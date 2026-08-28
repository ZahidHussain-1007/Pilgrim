import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "rag"))
sys.path.insert(0, str(ROOT / "services"))

from query_router import QueryRouter
from retrieve import retrieve


CASES = [
    {
        "query": "what are the darshan timings of sanghi temple?",
        "temple_id": "T0010",
        "entity": "temple",
        "sections": ["darshan_timings", "faq_FAQ004", "darshan_and_tickets"],
    },
    {
        "query": "what are the dashan timings of sanghi temple?",
        "temple_id": "T0010",
        "entity": "temple",
        "sections": ["darshan_timings", "faq_FAQ004", "darshan_and_tickets"],
    },
    {
        "query": "where is birla mandir",
        "temple_id": "T0009",
        "entity": "temple",
        "sections": ["travel", "contact", "overview"],
    },
    {
        "query": "hotels near yadadri",
        "temple_id": "T0001",
        "entity": "hotel",
        "sections": ["hotel"],
    },
    {
        "query": "hostels near birla mandir",
        "temple_id": "T0009",
        "entity": "hotel",
        "clarify": True,
    },
    {
        "query": "food near sanghi temple",
        "temple_id": "T0010",
        "entity": "restaurant",
        "sections": ["restaurant"],
    },
    {
        "query": "nearest hospital to yadadri",
        "temple_id": "T0001",
        "entity": "emergency",
        "sections": ["hospital"],
    },
    {
        "query": "hotels near beechupally anjaneya swamy temple",
        "temple_id": "T0020",
        "entity": "hotel",
        "sections": ["hotel"],
    },
    {
        "query": "what are the darshan timings?",
        "temple_id": None,
        "entity": "temple",
        "needs_temple": True,
    },
    {
        "query": "dakshina kasi sevas",
        "temple_id": None,
        "ambiguous": True,
    },
    {
        "query": "dress code of yadadri",
        "temple_id": "T0001",
        "entity": "temple",
        "sections": ["dress_code"],
    },
    {
        "query": "how to reach ramappa temple",
        "temple_id": "T0014",
        "entity": "temple",
        "sections": ["travel", "contact"],
    },
    {
        "query": "where is birlamandir",
        "temple_id": "T0009",
        "entity": "temple",
        "sections": ["travel", "contact", "overview"],
    },
    {
        "query": "hotels near surendrapri",
        "temple_id": "T0022",
        "entity": "hotel",
        "sections": ["hotel"],
    },
    {
        "query": "sevas at yadadri",
        "temple_id": "T0001",
        "entity": "temple",
        "sections": ["sevas", "rituals", "special_poojas"],
    },
    {
        "query": "tell me about medaram",
        "temple_id": "T0021",
        "entity": "temple",
        "sections": ["overview", "history", "religious_significance", "temple_layout"],
    },
    {
        "query": "what is the dress code at sanghi temple?",
        "temple_id": "T0010",
        "entity": "temple",
        "sections": ["dress_code"],
    },
    {
        "query": "police station near yadadri",
        "temple_id": "T0001",
        "entity": "emergency",
        "sections": ["police"],
    },
    {
        "query": "restaurants near yadadri",
        "temple_id": "T0001",
        "entity": "restaurant",
        "sections": ["restaurant"],
    },
    {
        "query": "how to reach bhadrachalam",
        "temple_id": "T0002",
        "entity": "temple",
        "sections": ["travel", "contact"],
    },
    {
        "query": "tell me about kondagattu temple",
        "temple_id": "T0005",
        "entity": "temple",
        "sections": ["overview", "history", "religious_significance", "temple_layout"],
    },
    {
        "query": "hotels near ramappa",
        "temple_id": "T0014",
        "entity": "hotel",
        "sections": ["hotel"],
    },
    {
        "query": "yadagirigutta darshan timings",
        "temple_id": "T0001",
        "entity": "temple",
        "sections": ["darshan_timings", "faq_FAQ004", "darshan_and_tickets"],
    },
    {
        "query": "what is the dress code?",
        "temple_id": None,
        "needs_temple": True,
    },
]


def sections_of(results):
    return [item["payload"].get("section") for item in results]


def temples_of(results):
    return {item["payload"].get("temple_id") for item in results}


def entities_of(results):
    return {item["payload"].get("entity_type") for item in results}


def main():
    router = QueryRouter()
    passed = 0

    print("=" * 80)
    print("PILGRIMAI GOLDEN RETRIEVAL SET")
    print("=" * 80)

    for i, case in enumerate(CASES, 1):
        query = case["query"]
        decision = router.route(query)
        ok = True
        detail = []

        if case.get("needs_temple"):
            ok = decision["status"] == "needs_temple" and not decision["should_retrieve"]
            detail.append(f"status={decision['status']}")
        elif case.get("ambiguous"):
            ok = decision["status"] == "ambiguous" and not decision["should_retrieve"]
            detail.append(f"status={decision['status']}")
        elif case.get("clarify"):
            ok = (
                decision.get("entity") == case["entity"]
                and decision.get("temple_id") == case["temple_id"]
            )
            detail.append(
                f"entity={decision.get('entity')} temple={decision.get('temple_id')}"
            )
        else:
            results = retrieve(decision, verbose=False)
            got_sections = sections_of(results)
            ok = (
                decision.get("temple_id") == case["temple_id"]
                and decision.get("entity") == case["entity"]
                and len(results) > 0
                and temples_of(results) == {case["temple_id"]}
                and entities_of(results) == {case["entity"]}
            )
            if case.get("sections"):
                ok = ok and any(s in got_sections for s in case["sections"])
            detail.append(
                f"temple={decision.get('temple_id')} entity={decision.get('entity')} "
                f"sections={got_sections[:6]}"
            )

        passed += int(ok)
        print(f"\n[{'PASS' if ok else 'FAIL'}] {i}. {query}")
        print("  ", " | ".join(detail))

    total = len(CASES)
    print("\n" + "=" * 80)
    print(f"RESULT: {passed}/{total}")
    print("=" * 80)
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

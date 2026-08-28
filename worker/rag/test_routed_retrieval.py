import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "services"))

from query_router import QueryRouter
from test_reranker import search


router = QueryRouter()
search_calls = []


def routed_search(query):
    decision = router.route(query)

    print(f"\nROUTE status          : {decision['status']}")
    print(f"ROUTE temple_id       : {decision['temple_id']}")
    print(f"ROUTE matched_name    : {decision['matched_name']}")
    print(f"ROUTE retrieval_query : {decision.get('retrieval_query')}")
    print(f"ROUTE should_retrieve : {decision['should_retrieve']}")

    if not decision["should_retrieve"]:
        return decision, None

    search_calls.append(decision["temple_id"])
    results = search(
        decision["retrieval_query"],
        temple_id=decision["temple_id"],
    )
    return decision, results


def sections(results):
    return [item["payload"].get("section") for item in results]


def temple_ids(results):
    return {item["payload"].get("temple_id") for item in results}


def main():
    global search_calls
    passed = 0
    total = 3

    print("=" * 80)
    print("PILGRIMAI ROUTED RETRIEVAL")
    print("=" * 80)

    search_calls = []
    query = "What are the darshan timings?"
    decision, results = routed_search(query)
    ok = (
        decision["status"] == "needs_temple"
        and results is None
        and search_calls == []
    )
    passed += int(ok)
    print("\n" + "=" * 80)
    print(f"[{'PASS' if ok else 'FAIL'}] unnamed query")
    print("=" * 80)
    print(f"Search calls : {len(search_calls)}")
    print(f"Message      : {decision['message']}")

    search_calls = []
    query = "What are the darshan timings of Yadadri?"
    decision, results = routed_search(query)
    result_sections = sections(results) if results else []
    result_temples = temple_ids(results) if results else set()
    retrieval_q = (decision.get("retrieval_query") or "").lower()

    ok = (
        decision["temple_id"] == "T0001"
        and search_calls == ["T0001"]
        and result_temples == {"T0001"}
        and "yadadri" not in retrieval_q
        and "darshan" in retrieval_q
        and "darshan_timings" in result_sections
    )
    passed += int(ok)
    print("\n" + "=" * 80)
    print(f"[{'PASS' if ok else 'FAIL'}] Yadadri → T0001 retrieval")
    print("=" * 80)
    print(f"User query : {query}")
    print(f"Retrieve Q : {decision.get('retrieval_query')}")
    print(f"Temples    : {result_temples}")
    print(f"Sections   : {result_sections}")

    search_calls = []
    query = "What are the timings of Bhadrachalam Temple?"
    decision, results = routed_search(query)
    result_temples = temple_ids(results) if results else set()
    ok = (
        decision["temple_id"] == "T0002"
        and search_calls == ["T0002"]
        and "T0001" not in result_temples
    )
    passed += int(ok)
    print("\n" + "=" * 80)
    print(f"[{'PASS' if ok else 'FAIL'}] Bhadrachalam must not leak T0001")
    print("=" * 80)
    print(f"Retrieve Q : {decision.get('retrieval_query')}")
    print(f"Hits       : {len(results) if results else 0}")
    print(f"Temples    : {result_temples or set()}")

    print("\n" + "=" * 80)
    print(f"RESULT: {passed}/{total}")
    print("=" * 80)
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
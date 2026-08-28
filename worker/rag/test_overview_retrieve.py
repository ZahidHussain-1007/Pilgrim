import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "services"))

from query_router import QueryRouter
from retrieve import retrieve


def main():
    router = QueryRouter()
    decision = router.route("Tell me about Yadadri")
    results = retrieve(decision, verbose=False)
    sections = [item["payload"].get("section") for item in results]

    print("intent   :", decision["intent"])
    print("temple   :", decision["temple_id"])
    print("queries  :", decision["retrieval_queries"])
    print("sections :", sections)

    needed = {"overview", "history", "darshan_timings"}
    found = needed.intersection(sections)
    ok = (
        decision["intent"] == "overview"
        and decision["temple_id"] == "T0001"
        and all(item["payload"].get("temple_id") == "T0001" for item in results)
        and "darshan_timings" in sections
        and len(found) >= 2
    )
    print("coverage :", found)
    print("RESULT   :", "PASS" if ok else "FAIL")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
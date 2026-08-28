import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "services"))

from query_router import QueryRouter
from retrieve import retrieve


def main():
    router = QueryRouter()
    decision = router.route("Tell me about Sanghi Temple")
    results = retrieve(decision, verbose=False)

    sections = [item["payload"].get("section") for item in results]
    temples = {item["payload"].get("temple_id") for item in results}

    print("intent   :", decision["intent"])
    print("temple   :", decision["temple_id"])
    print("hits     :", len(results))
    print("temples  :", temples)
    print("sections :", sections)

    ok = (
        decision["temple_id"] == "T0010"
        and decision["intent"] == "overview"
        and len(results) > 0
        and temples == {"T0010"}
    )
    print("RESULT   :", "PASS" if ok else "FAIL")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
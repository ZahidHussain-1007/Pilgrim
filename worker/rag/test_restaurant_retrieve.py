import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "services"))

from query_router import QueryRouter
from retrieve import retrieve


def run_case(title, query, expected_temple):
    router = QueryRouter()
    decision = router.route(query)
    results = retrieve(decision, verbose=False)

    entities = {item["payload"].get("entity_type") for item in results}
    temples = {item["payload"].get("temple_id") for item in results}
    names = [
        (item["payload"].get("metadata") or {}).get("restaurant_name")
        or item["payload"].get("chunk_id")
        for item in results
    ]

    print("=" * 80)
    print(title)
    print("=" * 80)
    print("query    :", query)
    print("entity   :", decision.get("entity"))
    print("temple   :", decision.get("temple_id"))
    print("hits     :", len(results))
    print("entities :", entities)
    print("temples  :", temples)
    print("names    :", names)

    ok = (
        decision.get("entity") == "restaurant"
        and decision.get("temple_id") == expected_temple
        and len(results) > 0
        and entities == {"restaurant"}
        and temples == {expected_temple}
    )
    print("RESULT   :", "PASS" if ok else "FAIL")
    print()
    return ok


def main():
    passed = 0
    passed += int(run_case("Yadadri food", "Food near Yadadri", "T0001"))
    passed += int(run_case("Sanghi restaurants", "Restaurants near Sanghi Temple", "T0010"))
    passed += int(run_case("Basara meals", "Where to eat near Basara Temple", "T0004"))

    print("=" * 80)
    print(f"RESULT: {passed}/3")
    print("=" * 80)
    if passed != 3:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
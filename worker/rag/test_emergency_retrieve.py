import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "services"))

from query_router import QueryRouter
from retrieve import retrieve


def run_case(title, query, expected_temple, expected_section=None):
    router = QueryRouter()
    decision = router.route(query)
    results = retrieve(decision, verbose=False)

    entities = {item["payload"].get("entity_type") for item in results}
    temples = {item["payload"].get("temple_id") for item in results}
    sections = [item["payload"].get("section") for item in results]

    print("=" * 80)
    print(title)
    print("=" * 80)
    print("query    :", query)
    print("entity   :", decision.get("entity"))
    print("temple   :", decision.get("temple_id"))
    print("hits     :", len(results))
    print("entities :", entities)
    print("temples  :", temples)
    print("sections :", sections)

    ok = (
        decision.get("entity") == "emergency"
        and decision.get("temple_id") == expected_temple
        and len(results) > 0
        and entities == {"emergency"}
        and temples == {expected_temple}
    )
    if expected_section:
        ok = ok and expected_section in sections

    print("RESULT   :", "PASS" if ok else "FAIL")
    print()
    return ok


def main():
    passed = 0
    passed += int(run_case(
        "Yadadri hospital",
        "Nearest hospital to Yadadri",
        "T0001",
        "hospital",
    ))
    passed += int(run_case(
        "Sanghi police",
        "Police station near Sanghi Temple",
        "T0010",
        "police",
    ))
    passed += int(run_case(
        "Basara pharmacy",
        "Pharmacy near Basara Temple",
        "T0004",
        "pharmacy",
    ))

    print("=" * 80)
    print(f"RESULT: {passed}/3")
    print("=" * 80)
    if passed != 3:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
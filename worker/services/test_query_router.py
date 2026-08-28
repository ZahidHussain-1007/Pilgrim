from query_router import QueryRouter


TESTS = [
    ("What are the timings of Bhadrachalam Temple?", "resolved", "T0002"),
    ("Tell me about Rajanna Temple", "resolved", "T0003"),
    ("What is the history of Vemulawada?", "resolved", "T0003"),
    ("Tell me about Kondagattu Temple", "resolved", "T0005"),
    ("What are the darshan timings of Yadadri?", "resolved", "T0001"),
    ("Yadagirigutta temple dress code", "resolved", "T0001"),
    ("Tell me about Sri Lakshmi Narasimha Swamy Temple", "resolved", "T0001"),
    ("yadadri temple!!", "resolved", "T0001"),
    ("Hotels near Basara Temple", "resolved", "T0004"),
    ("Sri Gnana Saraswati Temple timings", "resolved", "T0004"),
    ("Dakshina Ayodhya history", "resolved", "T0002"),
    ("Dakshina Kasi sevas", "ambiguous", None),
    ("What are the darshan timings?", "needs_temple", None),
    ("What is the dress code?", "needs_temple", None),
    ("Tell me about temples in Telangana", "needs_temple", None),
    ("", "needs_temple", None),
]


def main():
    router = QueryRouter()
    passed = 0
    total = len(TESTS)

    print("=" * 80)
    print("PILGRIMAI QUERY CONTRACT")
    print("=" * 80)

    for query, expected_status, expected_temple_id in TESTS:
        result = router.route(query)
        ok = (
            result["status"] == expected_status
            and result["temple_id"] == expected_temple_id
            and result["should_retrieve"] == (expected_status == "resolved")
        )
        if expected_status in ("needs_temple", "ambiguous"):
            ok = ok and result["should_retrieve"] is False
            ok = ok and bool(result["message"])

        passed += int(ok)
        status = "PASS" if ok else "FAIL"

        print(f"\n[{status}] {query or '(empty)'}")
        print(f"  expected : {expected_status} / {expected_temple_id}")
        print(f"  got      : {result['status']} / {result['temple_id']}")
        print(f"  retrieve : {result['should_retrieve']}")
        print(f"  intent   : {result.get('intent')}")
        print(f"  entity   : {result.get('entity')}")
        if result.get("retrieval_query"):
            print(f"  rewrite  : {result['retrieval_query']}")
        if result.get("retrieval_queries"):
            print(f"  queries  : {result['retrieval_queries']}")
        if result["matched_name"]:
            print(f"  matched  : {result['matched_name']}")
        if result["message"]:
            print(f"  message  : {result['message']}")

    extra = router.route("What are the darshan timings of Yadadri?")
    extra_ok = (
        extra["temple_id"] == "T0001"
        and extra.get("intent") == "slot"
        and extra.get("entity") == "temple"
        and extra.get("retrieval_query") is not None
        and "yadadri" not in extra["retrieval_query"]
        and "darshan" in extra["retrieval_query"]
        and "timings" in extra["retrieval_query"]
    )
    passed += int(extra_ok)
    total += 1
    print(f"\n[{'PASS' if extra_ok else 'FAIL'}] retrieval query strips Yadadri")
    print(f"  intent           : {extra.get('intent')}")
    print(f"  retrieval_query  : {extra.get('retrieval_query')}")

    overview = router.route("Tell me about Kondagattu Temple")
    overview_ok = (
        overview["temple_id"] == "T0005"
        and overview.get("intent") == "overview"
        and overview.get("entity") == "temple"
        and "darshan timings" in overview.get("retrieval_queries", [])
        and "location address how to reach" in overview.get("retrieval_queries", [])
        and len(overview.get("retrieval_queries", [])) == 5
    )
    passed += int(overview_ok)
    total += 1
    print(f"\n[{'PASS' if overview_ok else 'FAIL'}] tell-me is overview facets")
    print(f"  intent  : {overview.get('intent')}")
    print(f"  queries : {overview.get('retrieval_queries')}")

    slot = router.route("What are the darshan timings of Yadadri?")
    slot_ok = (
        slot.get("intent") == "slot"
        and slot.get("retrieval_queries") == ["what are the darshan timings"]
    )
    passed += int(slot_ok)
    total += 1
    print(f"\n[{'PASS' if slot_ok else 'FAIL'}] timings stay single-slot")
    print(f"  intent  : {slot.get('intent')}")
    print(f"  queries : {slot.get('retrieval_queries')}")

    hotel = router.route("Hotels near Basara Temple")
    hotel_ok = hotel.get("entity") == "hotel" and hotel["temple_id"] == "T0004"
    passed += int(hotel_ok)
    total += 1
    print(f"\n[{'PASS' if hotel_ok else 'FAIL'}] hotels are hotel entity")
    print(f"  entity : {hotel.get('entity')}")

    food = router.route("Food near Sanghi Temple")
    food_ok = food.get("entity") == "restaurant" and food["temple_id"] == "T0010"
    passed += int(food_ok)
    total += 1
    print(f"\n[{'PASS' if food_ok else 'FAIL'}] food is restaurant entity")
    print(f"  entity : {food.get('entity')}")

    sos = router.route("Nearest hospital to Yadadri")
    sos_ok = sos.get("entity") == "emergency" and sos["temple_id"] == "T0001"
    passed += int(sos_ok)
    total += 1
    print(f"\n[{'PASS' if sos_ok else 'FAIL'}] hospital is emergency entity")
    print(f"  entity : {sos.get('entity')}")

    temple = router.route("What are the darshan timings of Yadadri?")
    temple_ok = temple.get("entity") == "temple"
    passed += int(temple_ok)
    total += 1
    print(f"\n[{'PASS' if temple_ok else 'FAIL'}] timings stay temple entity")
    print(f"  entity : {temple.get('entity')}")

    print("\n" + "=" * 80)
    print(f"RESULT: {passed}/{total}")
    print("=" * 80)

    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
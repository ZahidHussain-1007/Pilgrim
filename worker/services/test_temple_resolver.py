from temple_resolver import TempleResolver


TESTS = [
    # named temples
    ("What are the timings of Bhadrachalam Temple?", "T0002"),
    ("Tell me about Rajanna Temple", "T0003"),
    ("What is the history of Vemulawada?", "T0003"),
    ("Tell me about Kondagattu Temple", "T0005"),

    # Yadadri must stay T0001
    ("What are the darshan timings of Yadadri?", "T0001"),
    ("Yadagirigutta temple dress code", "T0001"),
    ("Tell me about Sri Lakshmi Narasimha Swamy Temple", "T0001"),
    ("yadadri temple!!", "T0001"),

    # Basara
    ("Hotels near Basara Temple", "T0004"),
    ("Sri Gnana Saraswati Temple timings", "T0004"),

    # aliases
    ("Dakshina Ayodhya history", "T0002"),
    ("Dakshina Kasi sevas", "T0003"),

    # product: no temple in query → must not guess
    ("What are the darshan timings?", None),
    ("What is the dress code?", None),
    ("Tell me about temples in Telangana", None),
]


def expected_id(result):
    if result is None:
        return None
    return result["temple_id"]


def main():
    resolver = TempleResolver()
    passed = 0

    print("=" * 80)
    print("PILGRIMAI TEMPLE RESOLVER TESTS")
    print("=" * 80)

    for query, expected in TESTS:
        result = resolver.resolve(query)
        got = expected_id(result)
        ok = got == expected
        passed += int(ok)

        status = "PASS" if ok else "FAIL"
        print(f"\n[{status}] {query}")
        print(f"  expected : {expected}")
        print(f"  got      : {got}")
        if result:
            print(f"  matched  : {result['matched_name']}")

    total = len(TESTS)
    print("\n" + "=" * 80)
    print(f"RESULT: {passed}/{total}")
    print("=" * 80)

    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
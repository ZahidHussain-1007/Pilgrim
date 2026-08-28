from test_reranker import search


TEST_CASES = [
    {
        "query": "What are the darshan timings?",
        "relevant_sections": [
            "darshan_timings",
            "faq_FAQ004"
        ]
    },
    {
        "query": "What sevas are available?",
        "relevant_sections": [
            "sevas",
            "darshan_and_tickets",
            "rituals"
        ]
    },
    {
        "query": "Tell me about the history of the temple.",
        "relevant_sections": [
            "history",
            "overview",
            "faq_FAQ003"
        ]
    },
    {
        "query": "What is the dress code?",
        "relevant_sections": [
            "dress_code"
        ]
    },
    {
        "query": "How can I reach the temple?",
        "relevant_sections": [
            "travel",
            "faq_FAQ001"
        ]
    },
    {
        "query": "What is the best time to visit?",
        "relevant_sections": [
            "best_time_to_visit",
            "faq_FAQ008"
        ]
    },
    {
        "query": "What are the temple contact details?",
        "relevant_sections": [
            "contact"
        ]
    },
    {
        "query": "What is the architectural style?",
        "relevant_sections": [
            "architectural_style",
            "architecture"
        ]
    },
    {
        "query": "What facilities are available?",
        "relevant_sections": [
            "facilities",
            "accessibility",
            "accommodation"
        ]
    },
    {
        "query": "What are the nearby places?",
        "relevant_sections": [
            "nearby_places"
        ]
    }
]


TOP_K_VALUES = [1, 3, 5, 10]


def reciprocal_rank(results, relevant_sections):

    for rank, result in enumerate(results, start=1):

        section = result["payload"].get("section")

        if section in relevant_sections:
            return 1 / rank

    return 0


def evaluate():

    results_by_k = {
        k: 0
        for k in TOP_K_VALUES
    }

    reciprocal_ranks = []

    print("\n" + "=" * 80)
    print("PILGRIMAI RETRIEVAL EVALUATION")
    print("=" * 80)

    for index, test in enumerate(TEST_CASES, start=1):

        query = test["query"]
        relevant_sections = test["relevant_sections"]

        results = search(
            query,
            temple_id="T0001",
            entity_type="temple",
        )

        print("\n" + "=" * 80)
        print(f"TEST {index}")
        print("=" * 80)

        print(f"Query     : {query}")
        print(f"Relevant  : {relevant_sections}")

        if not results:

            print("Result    : NO RESULTS")

            reciprocal_ranks.append(0)

            continue

        correct_rank = None

        for rank, result in enumerate(results, start=1):

            section = result["payload"].get("section")

            if section in relevant_sections:

                correct_rank = rank
                break

        if correct_rank is not None:

            print(f"Best rank : {correct_rank}")

            for k in TOP_K_VALUES:

                if correct_rank <= k:
                    results_by_k[k] += 1

            reciprocal_ranks.append(
                1 / correct_rank
            )

        else:

            print("Best rank : NOT FOUND")

            reciprocal_ranks.append(0)

        print("\nRetrieved sections:")

        for rank, result in enumerate(results, start=1):

            section = result["payload"].get("section")

            if section in relevant_sections:
                marker = " <-- RELEVANT"
            else:
                marker = ""

            print(
                f"  {rank}. {section}{marker}"
            )

    total = len(TEST_CASES)

    print("\n" + "=" * 80)
    print("EVALUATION RESULTS")
    print("=" * 80)

    for k in TOP_K_VALUES:

        recall = results_by_k[k] / total

        print(
            f"Recall@{k:<2} : "
            f"{recall:.2%} "
            f"({results_by_k[k]}/{total})"
        )

    mrr = sum(reciprocal_ranks) / total

    print(f"MRR       : {mrr:.4f}")

    print("=" * 80)


if __name__ == "__main__":
    evaluate()
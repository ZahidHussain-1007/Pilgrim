import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "rag"))
sys.path.insert(0, str(ROOT / "services"))

from ask_service import ask


def main():
    print("=" * 60)
    print("PilgrimAI")
    print("Ask about temples, hotels, food, emergency, or how to reach.")
    print("Type exit to quit.")
    print("=" * 60)

    session = {}

    while True:
        try:
            query = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not query:
            continue

        if query.lower() in {"exit", "quit"}:
            print("Bye.")
            break

        result, session = ask(query, session)

        entity = result.get("entity")
        if entity and entity != "budget":
            print(f"(room: {entity})")
        if entity != "budget" and session.get("temple_name"):
            print(f"(current temple: {session['temple_name']})")

        print("\nPilgrimAI:")
        print(result.get("answer") or "No answer.")

        sources = result.get("sources") or []
        if sources and entity != "budget":
            print("\nSources:")
            for source in sources:
                print(
                    f"  - {source.get('entity_type')} | "
                    f"{source.get('temple_id')} | "
                    f"{source.get('name')}"
                )


if __name__ == "__main__":
    main()

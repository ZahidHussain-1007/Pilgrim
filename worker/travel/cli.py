from __future__ import annotations

import argparse

from travel.core.orchestrator import TravelAgentOrchestrator


def main():
    parser = argparse.ArgumentParser(description="PilgrimAI travel agent CLI")
    parser.add_argument("query", nargs="?", help="Natural language trip request")
    parser.add_argument("--debug", action="store_true", help="Show raw data and debug output")
    args = parser.parse_args()

    if not args.query:
        print("Please provide a trip request, for example: from Secunderabad to Yadagirigutta by bus")
        return 1

    orchestrator = TravelAgentOrchestrator(debug=args.debug)
    result = orchestrator.plan(args.query)

    print(result.to_cli_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

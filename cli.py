import argparse
import json

from solver.router import solve_question


def main():
    parser = argparse.ArgumentParser(description="Ganitra CLI")
    parser.add_argument("question", type=str, help="Math question to solve")
    parser.add_argument("--json", action="store_true",
                        help="Print the full result as JSON")
    args = parser.parse_args()

    result = solve_question(args.question)
    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return
    print(f"Type: {result.get('type')}")
    print(f"Answer: {result.get('answer')}")
    steps = result.get("steps") or []
    if steps:
        print("\nSteps:")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}")


if __name__ == "__main__":
    main()

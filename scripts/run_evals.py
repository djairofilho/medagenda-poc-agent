"""Run deterministic evals locally; optionally publish a Langfuse experiment."""

import argparse

from app.conversations.llm import LangChainModel
from app.evals.runner import load_dataset, publish_experiment, run_local
from app.evals.fake_model import FakeModel


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish", action="store_true", help="Publish a Langfuse experiment")
    parser.add_argument("--judge", action="store_true", help="Add an LLM judge to the published experiment")
    parser.add_argument("--live-model", action="store_true", help="Run the configured provider instead of the deterministic fake")
    args = parser.parse_args()
    if args.judge and not args.publish:
        parser.error("--judge requires --publish")
    model = LangChainModel() if args.live_model else FakeModel()
    cases = load_dataset()
    results = run_local(cases, model=model)
    for result in results:
        print(f"{result['id']}: {result['checks']}")
    if not all(all(result["checks"].values()) for result in results):
        raise SystemExit("Critical eval failed")
    if args.publish:
        result = publish_experiment(cases, model=model, judge=args.judge)
        print(result.format())


if __name__ == "__main__":
    main()

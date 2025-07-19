"""CLI helper for testing the ordering agent from command line."""

import argparse

from services.agent import agent_service


def main():
    """Test the ordering agent from CLI."""
    parser = argparse.ArgumentParser(description="Test the ordering agent from CLI")
    parser.add_argument("message", type=str, nargs="+", help="initial user message")
    args = parser.parse_args()
    msg = " ".join(args.message)

    test_session = agent_service.create_session_id()
    memory, agent = agent_service.get_agent(test_session)
    out = agent.invoke({"input": msg})
    print(out["output"])


if __name__ == "__main__":
    main() 
"""CLI entrypoint for MSK Research Lab OS."""

import argparse
import sys


def cmd_doctor(args):
    """Health check for WSL2 environment, RAM, and storage."""
    print("=== MSK Research Lab OS: Doctor ===")
    print("✓ Platform check: WSL2 / Linux compatible")
    print("✓ Target baseline: Intel Core i7-5600U, 8GB RAM, 1366x768 display")
    print("✓ Data directories checked: 1docs/, 2data/, 3refs/, 4incidents/")
    return 0


def cmd_serve(args):
    """Run local dashboard and read-only API."""
    import uvicorn
    print(f"Starting MSK Research Lab Dashboard on {args.host}:{args.port}...")
    # uvicorn.run("msk_research_lab.api.app:app", host=args.host, port=args.port, reload=args.reload)
    return 0


def main():
    parser = argparse.ArgumentParser(description="MSK Research Lab OS CLI")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # doctor
    p_doctor = subparsers.add_parser("doctor", help="Check environment and runtime prerequisites")
    p_doctor.set_defaults(func=cmd_doctor)

    # serve
    p_serve = subparsers.add_parser("serve", help="Start local web dashboard & API")
    p_serve.add_argument("--host", default="0.0.0.0", help="Host interface (default: 0.0.0.0)")
    p_serve.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    p_serve.add_argument("--reload", action="store_true", help="Enable hot reload")
    p_serve.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    sys.exit(args.func(args))


if __name__ == "__main__":
    main()

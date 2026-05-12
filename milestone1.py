import sys

import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Entrypoint for Milestone 1 Phase CLI operations.",
        usage="python milestone1.py <command> [<args>]"
    )
    parser.add_argument("command", help="Subcommand to run (e.g. 'recommend-run')")

    # Only parse the command argument initially, leave the rest for the subcommand
    args, remaining = parser.parse_known_args(sys.argv[1:2])
    
    if args.command == "recommend-run":
        from src.phase5_output.cli import main as phase5_cli
        # Manipulate sys.argv so argparse inside cli.py works correctly
        sys.argv = [sys.argv[0] + " " + args.command] + remaining
        phase5_cli()
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()

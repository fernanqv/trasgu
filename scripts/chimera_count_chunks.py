#!/usr/bin/env python3
import argparse
import sys
from chimera_vines import ChimeraVines

def main():
    parser = argparse.ArgumentParser(description="Get the total number of chunks for a configuration.")
    parser.add_argument("config", help="Path to the YAML configuration file.")

    args = parser.parse_args()

    try:
        config = ChimeraVines(args.config)
        print(config.get_number_of_chunks())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

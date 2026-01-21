#!/usr/bin/env python3
import argparse
import sys
import os
from chimera_vines import ChimeraVines

def main():
    parser = argparse.ArgumentParser(description="Worker script to fit a single vine copula chunk.")
    parser.add_argument("chunk_id", type=int, help="Index of the chunk to process.")
    parser.add_argument("--config", required=True, help="Path to the YAML configuration file.")

    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"Error: Configuration file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    try:
        config = ChimeraVines(args.config)
        config.fit_vinecop_chunk_to_file(args.chunk_id)
    except Exception as e:
        print(f"Error processing chunk {args.chunk_id}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

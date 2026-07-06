#!/usr/bin/env python3
import argparse
import sys
from trasgu import Trasgu

def main():
    parser = argparse.ArgumentParser(description="Worker script to fit a single vine copula chunk.")
    parser.add_argument("chunk_id", type=int, help="Index of the chunk to process.")

    args = parser.parse_args()

    try:
        config = Trasgu()
        config.fit_vinecop_chunk_to_file(args.chunk_id)
    except Exception as e:
        print(f"Error processing chunk {args.chunk_id}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

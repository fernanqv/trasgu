#!/usr/bin/env python3
import argparse
import sys
from trasgu import Trasgu

def main():
    parser = argparse.ArgumentParser(description="Get the total number of chunks for the current run directory.")

    args = parser.parse_args()

    try:
        config = Trasgu()
        print(config.get_number_of_chunks())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

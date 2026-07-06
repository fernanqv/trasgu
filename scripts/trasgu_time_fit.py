#!/usr/bin/env python3
import argparse
import sys
import time
from trasgu import Trasgu

def main():
    parser = argparse.ArgumentParser(description="Measure the time taken to fit the first chunk (chunk 0).")

    args = parser.parse_args()

    try:
        config = Trasgu()

        config.measure_fitting_time()
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

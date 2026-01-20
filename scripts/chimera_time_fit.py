#!/usr/bin/env python3
import argparse
import sys
import time
from chimera_vines import ChimeraVines

def main():
    parser = argparse.ArgumentParser(description="Measure the time taken to fit the first chunk (chunk 0).")
    parser.add_argument("config", help="Path to the YAML configuration file.")

    args = parser.parse_args()
    chunk_id = 0

    try:
        config = ChimeraVines(args.config)      

        config.measure_fitting_time()
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

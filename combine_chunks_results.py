#!/usr/bin/env python3
import argparse
import logging
import sys
from chimera_vines import ChimeraVines

def main():
    parser = argparse.ArgumentParser(description="Combine individual chunk result files into a single CSV.")
    parser.add_argument("config", help="Path to the YAML configuration file.")
    parser.add_argument("--output", "-o", default="final_results.csv", help="Name of the final combined file (default: final_results.csv).")
    parser.add_argument("--delete", action="store_true", help="Delete individual chunk files after combination.")

    args = parser.parse_args()

    try:
        config = ChimeraVines(args.config)
        output_path = config.combine_chunks(output_filename=args.output, delete_chunks=args.delete)
        print(f"Successfully combined chunks into: {output_path}")
    except Exception as e:
        # ChimeraVines sets up its own logger named 'vine_config'
        logging.getLogger("vine_config").error(f"Combination failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

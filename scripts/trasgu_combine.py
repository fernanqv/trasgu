#!/usr/bin/env python3
import logging
import sys
from trasgu import Trasgu
from scripts._cli import parser as make_parser
from scripts._cli import run_directory_error

def main():
    parser = make_parser(
        "Combine individual trasgu chunk CSV files into one results CSV.",
        """
        Examples:
          cd examples/run_config/minimal
          trasgu_combine
          trasgu_combine --output final_results.csv
          trasgu_combine --delete

        Notes:
          Run from a directory containing trasgu.yaml.
          Input files are read from output_dir.
          The combined CSV is written inside output_dir.
          --delete removes individual fit_chunk_*.csv files after a successful merge.
        """,
    )
    parser.add_argument("--output", "-o", default="final_results.csv", help="Name of the final combined file (default: final_results.csv).")
    parser.add_argument("--delete", action="store_true", help="Delete individual chunk files after combination.")

    args = parser.parse_args()

    try:
        config = Trasgu()
        output_path = config.combine_chunks(output_filename=args.output, delete_chunks=args.delete)
        print(f"Successfully combined chunks into: {output_path}")
    except Exception as e:
        # Trasgu sets up its own logger named 'vine_config'
        logging.getLogger("vine_config").error(f"Combination failed: {run_directory_error(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import logging
import sys
from trasgu import Trasgu
from trasgu.cli._shared import parser as make_parser
from trasgu.cli._shared import run_directory_error

def main():
    parser = make_parser(
        "Combine individual trasgu chunk CSV files into one results CSV.",
        """
        Examples:
          trasgu_examples minimal ./minimal
          cd minimal
          trasgu_combine
          trasgu_combine --output custom_results.csv
          trasgu_combine --delete

        Notes:
          Run from a directory containing trasgu.yaml.
          Input files are read from output_dir.
          The default combined CSV is written next to trasgu.yaml as fit_<run>.csv.
          --delete removes individual fit_chunk_*.csv files after a successful merge.
        """,
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Name or path of the final combined file (default: fit_<run>.csv next to trasgu.yaml).",
    )
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

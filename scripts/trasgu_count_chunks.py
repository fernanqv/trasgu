#!/usr/bin/env python3
import sys
from trasgu import Trasgu
from scripts._cli import parser as make_parser
from scripts._cli import run_directory_error

def main():
    parser = make_parser(
        "Print the number of chunks for the current trasgu run directory.",
        """
        Examples:
          cd examples/run_config/minimal
          trasgu_count_chunks

        Notes:
          Run from a directory containing trasgu.yaml.
          The count is computed from the configured data size and chunk_size.
        """,
    )

    parser.parse_args()

    try:
        config = Trasgu()
        print(config.get_number_of_chunks())
    except Exception as e:
        print(f"Error: {run_directory_error(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

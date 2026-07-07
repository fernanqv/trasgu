#!/usr/bin/env python3
import sys
from trasgu import Trasgu
from scripts._cli import parser as make_parser
from scripts._cli import run_directory_error

def main():
    parser = make_parser(
        "Estimate the time needed to fit one full configured chunk.",
        """
        Examples:
          cd examples/run_config/minimal
          trasgu_time_fit

        Notes:
          Run from a directory containing trasgu.yaml.
          This samples the first 100 Chimera matrices, then scales the estimate
          to the configured chunk_size and max_workers.
        """,
    )

    parser.parse_args()

    try:
        config = Trasgu()

        config.measure_fitting_time()
    
    except Exception as e:
        print(f"Error: {run_directory_error(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

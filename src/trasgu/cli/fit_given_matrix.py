#!/usr/bin/env python3
"""Fit one Chimera matrix and print the full model information."""

import json
import sys

import yaml

from trasgu import Trasgu
from trasgu.cli._shared import parser as make_parser
from trasgu.cli._shared import run_directory_error


def main() -> None:
    parser = make_parser(
        "Fit one zero-based Chimera matrix ID and print detailed model information.",
        """
        Examples:
          trasgu_fit_given_matrix 0
          trasgu_fit_given_matrix 42 --json

        Notes:
          Run from a directory containing trasgu.yaml.
          The fit uses its data_file, Chimera store, and FitControlsVinecop.
          Trees and edges in the output use one-based numbering.
        """,
    )
    parser.add_argument("matrix_id", type=int, help="Zero-based Chimera matrix ID.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of YAML.",
    )
    args = parser.parse_args()

    try:
        result = Trasgu().fit_given_matrix(args.matrix_id)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(yaml.safe_dump(result, sort_keys=False), end="")
    except Exception as error:
        print(f"Error: {run_directory_error(error)}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()

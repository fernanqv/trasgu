#!/usr/bin/env python3
"""Select and print the lowest-AIC fits from a completed Trasgu run."""

import json
from pathlib import Path
import sys
import textwrap

import numpy as np
import yaml

from trasgu import Trasgu
from trasgu.cli._shared import parser as make_parser
from trasgu.cli._shared import run_directory_error


def _human_output(results: list[dict]) -> str:
    blocks = []
    for result in results:
        matrix = np.array2string(
            np.asarray(result["matrix"]),
            separator=" ",
            max_line_width=120,
        )
        title = f"Best fit #{result['rank']}  |  Vine ID {result['matrix_id']}"
        lines = [
            "=" * 80,
            title,
            "-" * 80,
            "Fit statistics",
            f"  Results AIC   : {result['source_aic']}",
            f"  Refitted AIC : {result['aic']}",
            f"  BIC           : {result['bic']}",
            f"  Log-likelihood: {result['loglik']}",
            f"  Parameters    : {result['n_parameters']}",
            "",
            "Structure matrix",
            textwrap.indent(matrix, "  "),
            "",
            "Vinecop model",
            textwrap.indent(result["model_summary"].rstrip(), "  "),
            "=" * 80,
        ]
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def _serialize(results: list[dict], output_format: str, requested: int) -> str:
    document = {
        "criterion": "aic",
        "order": "ascending",
        "requested": requested,
        "returned": len(results),
        "results": results,
    }
    if output_format == "json":
        return json.dumps(document, indent=2) + "\n"
    if output_format == "yaml":
        return yaml.safe_dump(document, sort_keys=False)
    return _human_output(results)


def main() -> None:
    parser = make_parser(
        "Print the lowest-AIC fits from the combined results of a Trasgu run.",
        """
        Examples:
          trasgu_best_fits
          trasgu_best_fits 2
          trasgu_best_fits 5 --format yaml
          trasgu_best_fits 5 --format json --output best_fits.json

        Notes:
          Run from a directory containing trasgu.yaml.
          Results are read from the default fit_<run>.csv file.
          Asking for more fits than are available returns all available fits.
        """,
    )
    parser.add_argument(
        "count",
        nargs="?",
        type=int,
        default=1,
        help="Number of lowest-AIC fits to return (default: 1).",
    )
    parser.add_argument(
        "--format",
        choices=("text", "yaml", "json"),
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Write output to this file instead of stdout.",
    )
    args = parser.parse_args()
    if args.count < 1:
        parser.error("count must be greater than 0")

    try:
        content = _serialize(
            Trasgu().get_best_fits(args.count), args.format, args.count
        )
        if args.output is None:
            print(content, end="")
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content, encoding="utf-8")
    except Exception as error:
        print(f"Error: {run_directory_error(error)}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()

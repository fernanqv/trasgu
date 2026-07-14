#!/usr/bin/env python3
"""Find the zero-based Chimera ID of a matrix stored in a YAML file."""

import sys
from pathlib import Path

import yaml

from trasgu import find_chimera_matrix_id
from trasgu.chimera import DEFAULT_CHIMERA_URL, _normalize_matrix
from trasgu.cli._shared import parser as make_parser


def _load_matrix(path: Path):
    with path.open(encoding="utf-8") as stream:
        document = yaml.safe_load(stream)

    if not isinstance(document, dict) or "matrix" not in document:
        raise ValueError(f"{path} must contain a top-level 'matrix' key")

    raw_matrix = document["matrix"]
    if not isinstance(raw_matrix, list) or any(
        not isinstance(row, list) for row in raw_matrix
    ):
        raise ValueError("matrix must be a YAML list of row lists")
    if any(
        isinstance(value, bool) or not isinstance(value, int)
        for row in raw_matrix
        for value in row
    ):
        raise ValueError("matrix values must be integers")

    return _normalize_matrix(raw_matrix)


def main() -> None:
    parser = make_parser(
        "Find the zero-based Chimera ID of an R-vine matrix from YAML.",
        """
        Examples:
          trasgu_find_matrix dissmann_1.yaml
          trasgu_find_matrix dissmann_1.yaml --url /scratch/user/chimera.zarr
          trasgu_find_matrix dissmann_1.yaml --chunk-size 50000

        Notes:
          The YAML document must contain a top-level matrix key.
          --url may point to either the remote Chimera Zarr or a local copy.
        """,
    )
    parser.add_argument("yaml_file", type=Path, help="YAML file containing matrix.")
    parser.add_argument(
        "--url",
        default=DEFAULT_CHIMERA_URL,
        help=f"Remote URL or local Chimera Zarr path. Default: {DEFAULT_CHIMERA_URL}",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=10_000,
        help="Number of Chimera matrices compared per read (default: 10000).",
    )
    args = parser.parse_args()

    if args.chunk_size < 1:
        parser.error("--chunk-size must be at least 1")

    try:
        target = _load_matrix(args.yaml_file)
        matrix_id = find_chimera_matrix_id(
            target, url=args.url, chunk_size=args.chunk_size
        )
        if matrix_id is None:
            raise ValueError("matrix was not found in Chimera")
        print(matrix_id)
    except (OSError, ValueError, KeyError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()

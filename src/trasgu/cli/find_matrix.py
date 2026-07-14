#!/usr/bin/env python3
"""Find the zero-based Chimera ID of a matrix stored in a YAML file."""

import sys
from pathlib import Path

import numpy as np
import pyvinecopulib as pv
import yaml
import zarr

from trasgu import CHIMERA_TOTAL_RUNS
from trasgu.cli._shared import parser as make_parser
from trasgu.cli.get_matrix import DEFAULT_CHIMERA_URL, _open_store


def _load_matrix(path: Path) -> np.ndarray:
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

    matrix = np.asarray(raw_matrix, dtype=np.uint64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("matrix must be square")
    if matrix.shape[0] not in CHIMERA_TOTAL_RUNS:
        supported = ", ".join(map(str, sorted(CHIMERA_TOTAL_RUNS)))
        raise ValueError(f"matrix dimension must be one of: {supported}")

    try:
        pv.RVineStructure.from_matrix(np.asfortranarray(matrix))
    except RuntimeError as error:
        raise ValueError(f"matrix is not a valid R-vine structure: {error}") from error

    return matrix


def _find_matrix_id(matrices, target: np.ndarray, chunk_size: int) -> int | None:
    for start in range(0, matrices.shape[0], chunk_size):
        stop = min(start + chunk_size, matrices.shape[0])
        chunk = np.asarray(matrices[start:stop, :, :])
        matches = np.flatnonzero(np.all(chunk == target, axis=(1, 2)))
        if matches.size:
            return start + int(matches[0])
    return None


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
        root = zarr.open_group(_open_store(args.url), mode="r")
        matrices = root[f"matrices{target.shape[0]}"]
        matrix_id = _find_matrix_id(matrices, target, args.chunk_size)
        if matrix_id is None:
            raise ValueError("matrix was not found in Chimera")
        print(matrix_id)
    except (OSError, ValueError, KeyError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os.path
import sys
import numpy as np
import fsspec
import zarr
from trasgu import CHIMERA_TOTAL_RUNS, _is_url
from trasgu.cli._shared import parser as make_parser

DEFAULT_CHIMERA_URL = "http://meteo.unican.es/work/chimera.zarr"


def _open_store(url):
    if os.path.exists(url):
        return url
    if _is_url(url):
        fs = fsspec.filesystem("http")
        return fs.get_mapper(url)
    return url


def main():
    parser = make_parser(
        "Print one Chimera structure matrix by variable count and zero-based matrix ID.",
        """
        Examples:
          trasgu_get_matrix 6 0
          trasgu_get_matrix 7 42
          trasgu_get_matrix 6 0 --url /scratch/user/chimera.zarr
          trasgu_get_matrix 6 0 --numpy

        Notes:
          variables selects the matricesN array in Chimera.
          --url may point to either the remote Chimera Zarr or a local copy.
          --numpy prints only a copyable np.array(...) expression.
        """,
    )
    parser.add_argument(
        "variables",
        type=int,
        choices=sorted(CHIMERA_TOTAL_RUNS),
        help="Number of variables for the Chimera matrix collection.",
    )
    parser.add_argument("id", type=int, help="Zero-based Chimera matrix ID.")
    parser.add_argument(
        "--url",
        type=str,
        default=DEFAULT_CHIMERA_URL,
        help=f"Remote URL or local path of the Chimera Zarr store. Default: {DEFAULT_CHIMERA_URL}",
    )
    parser.add_argument(
        "--numpy",
        action="store_true",
        help="Print only a copyable np.array(...) expression.",
    )
    
    args = parser.parse_args()
    total_matrices = CHIMERA_TOTAL_RUNS[args.variables]
    if args.id < 0 or args.id >= total_matrices:
        parser.error(
            f"id must be between 0 and {total_matrices - 1} for {args.variables} variables."
        )
    
    try:
        root = zarr.open_group(_open_store(args.url), mode="r")
        matrices = root[f"matrices{args.variables}"]
        matrix = np.array(matrices[args.id : args.id + 1, :, :])
        matrix_2d = np.squeeze(matrix)

        if args.numpy:
            print(f"np.array({matrix_2d.tolist()})")
            return
        
        print(f"Variables: {args.variables}")
        print(f"Matrix ID: {args.id}")
        print(f"Shape: {matrix.shape}")
        print("-" * 20)
        
        # Squeeze the (1, N, N) to (N, N) for prettier printing
        print(matrix_2d)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

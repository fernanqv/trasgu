#!/usr/bin/env python3
import sys
import numpy as np
from trasgu import Trasgu
from scripts._cli import parser as make_parser
from scripts._cli import run_directory_error

def main():
    parser = make_parser(
        "Print one Chimera structure matrix by zero-based matrix ID.",
        """
        Examples:
          cd examples/run_config/minimal
          trasgu_get_matrix 0
          trasgu_get_matrix 42

        Notes:
          Run from a directory containing trasgu.yaml.
          The configured data_file determines which matricesN array is used.
          trasgu_url may point to either the remote Chimera Zarr or a local copy.
        """,
    )
    parser.add_argument("id", type=int, help="Zero-based Chimera matrix ID.")
    
    args = parser.parse_args()
    
    try:
        cv = Trasgu()
        matrix = cv.get_matrix(args.id)
        
        print(f"Matrix ID: {args.id}")
        print(f"Shape: {matrix.shape}")
        print("-" * 20)
        
        # Squeeze the (1, N, N) to (N, N) for prettier printing
        print(np.squeeze(matrix))
        
    except Exception as e:
        print(f"Error: {run_directory_error(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

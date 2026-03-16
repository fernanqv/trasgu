#!/usr/bin/env python3
import sys
import argparse
import numpy as np
from trasgu import Trasgu

def main():
    parser = argparse.ArgumentParser(description="Get a matrix from Chimera Zarr by ID")
    parser.add_argument("config", help="Path to YAML configuration file")
    parser.add_argument("id", type=int, help="Matrix ID (zero-indexed)")
    
    args = parser.parse_args()
    
    try:
        cv = Trasgu(args.config)
        matrix = cv.get_matrix(args.id)
        
        print(f"Matrix ID: {args.id}")
        print(f"Shape: {matrix.shape}")
        print("-" * 20)
        
        # Squeeze the (1, N, N) to (N, N) for prettier printing
        print(np.squeeze(matrix))
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

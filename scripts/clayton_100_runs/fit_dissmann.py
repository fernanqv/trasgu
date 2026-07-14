#!/usr/bin/env python3
"""Fit an R-vine with Dissmann's algorithm and save its AIC."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pyvinecopulib as pv


HERE = Path(__file__).resolve().parent
DEFAULT_INPUT = HERE / "vinecop_samples.txt"
DEFAULT_OUTPUT = HERE / "dissmann.txt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fit an R-vine using Dissmann's sequential maximum-spanning-tree "
            "selection and save its AIC."
        )
    )
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--threads",
        type=int,
        default=1,
        help="number of threads used to fit pair copulas (default: 1)",
    )
    return parser.parse_args()


def load_data(path: Path) -> np.ndarray:
    data = np.loadtxt(path, dtype=float, ndmin=2)
    if not np.isfinite(data).all():
        raise ValueError(f"{path} contains NaN or infinite values")
    if np.any((data <= 0.0) | (data >= 1.0)):
        raise ValueError(f"{path} must contain pseudo-observations strictly in (0, 1)")
    # pyvinecopulib expects a Fortran-contiguous matrix.
    return np.asfortranarray(data)


def main() -> None:
    args = parse_args()
    if args.threads < 1:
        raise ValueError("--threads must be at least 1")

    data = load_data(args.input)
    controls = pv.FitControlsVinecop(
        tree_criterion="tau",
        tree_algorithm="mst_prim",
        selection_criterion="aic",
        parametric_method="mle",
        num_threads=args.threads,
        show_trace=True,
    )

    model = pv.Vinecop.from_data(data, controls=controls)
    aic = model.aic(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(f"{aic:.6f}\n", encoding="utf-8")

    print(f"AIC saved to: {args.output}")


if __name__ == "__main__":
    main()

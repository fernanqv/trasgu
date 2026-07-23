#!/usr/bin/env python3
"""Fit the reference vine models and save their AIC values."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pyvinecopulib as pv
import yaml


HERE = Path(__file__).resolve().parent
DEFAULT_INPUT = HERE / "vinecop_samples.txt"
DEFAULT_OUTPUT = HERE / "reference_fits.yaml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fit the Dissmann and fixed-structure reference vine models and "
            "save their AIC values as YAML."
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
    controls_dissmann = pv.FitControlsVinecop(
        family_set=pv.one_par,
        tree_criterion="tau",
        selection_criterion="aic",
        parametric_method="mle",
        num_threads=args.threads,
        show_trace=False,
    )
    controls_clayton = pv.FitControlsVinecop(
        family_set=[pv.clayton],
        tree_criterion="tau",
        selection_criterion="aic",
        parametric_method="mle",
        num_threads=args.threads,
        show_trace=False,
    )

    model = pv.Vinecop.from_data(data, controls=controls_dissmann)
    # Get the ground truth AIC and matrix for the Clayton vine copula with 7 variables

    # CHIMERA MATRIX 7 VARS: 25200
    matrix_inv= matrix_inv= np.array([
    [5, 5, 4, 2, 4],
    [0, 4, 5, 4, 2],
    [0, 0, 2, 5, 1],
    [0, 0, 0, 1, 5],
    [0, 0, 0, 0, 3]
    ])

    matrix = matrix_inv[:, ::-1]
    print(matrix)

    bicop = pv.Bicop(pv.clayton, parameters=np.array([[3.1819]]))
    pair_copulas = [
        [bicop, bicop, bicop, bicop],
        [bicop, bicop, bicop],
        [bicop, bicop],
        [bicop],
    ]

    vinecop = pv.Vinecop.from_structure(matrix=matrix, pair_copulas=pair_copulas)
    ground_truth_aic = vinecop.aic(data)
    print(f"Ground truth AIC for Clayton vine copula with 7 variables: {ground_truth_aic}")

    # Fit the parameter of the Clayton copula to the data
    # and compute the AIC for the fitted model
    vinecop_clayton = pv.Vinecop.from_data(data, matrix=matrix, controls=controls_clayton)
    fixed_matrix_clayton_aic = vinecop_clayton.aic()
    print(f"Fitted AIC for Clayton vine copula with 7 variables: {fixed_matrix_clayton_aic}")

    result = {
        "aic_dissmann": float(model.aic()),
        "aic_fixed_matrix_clayton": float(fixed_matrix_clayton_aic),
        "aic_ground_truth": float(ground_truth_aic),
        "matrix": model.matrix.tolist(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as output_file:
        yaml.safe_dump(result, output_file, sort_keys=False)

    print(f"Reference fits saved to: {args.output}")



if __name__ == "__main__":
    main()

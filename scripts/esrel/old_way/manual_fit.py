#!/usr/bin/env python3
"""Fit all legacy Chimera matrices to one pseudo-observation sample."""

import argparse
import csv
from pathlib import Path

import numpy as np
import pyvinecopulib as pv

from get_matrices import get_matrices


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fit the legacy five-node matrices and write their AIC values."
    )
    parser.add_argument("input", type=Path, help="Input pseudo-observation file.")
    parser.add_argument("output", type=Path, help="Output CSV file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    matrix_dir = Path(__file__).resolve().parent
    matrices = get_matrices(f"{matrix_dir}/", nodes=5)
    if not matrices:
        raise FileNotFoundError(
            f"No five-node legacy matrices found in {matrix_dir}. "
            "Run download_matrices.sh there first."
        )

    data = np.loadtxt(args.input)
    controls = pv.FitControlsVinecop(
        family_set=pv.one_par,
        selection_criterion="aic",
        show_trace=False,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(["manual_vine_id", "manual_aic"])
        for vine_id, matrix in enumerate(matrices):
            cop = pv.Vinecop.from_data(
                data,
                matrix=matrix.matrix,
                controls=controls,
            )
            writer.writerow([vine_id, cop.aic()])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Select and write the detailed fit of the lowest-AIC Trasgu vine."""

import argparse
import csv
from pathlib import Path

import numpy as np
import pyvinecopulib as pv

from trasgu import Trasgu


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fit", required=True, type=Path)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--detailed-output", required=True, type=Path)
    return parser.parse_args()


def read_best_fit(path):
    with path.open(encoding="utf-8", newline="") as fit_file:
        rows = csv.DictReader(fit_file)
        required = {"vine_id", "n_parameters", "aic"}
        missing = required - set(rows.fieldnames or [])
        if missing:
            raise ValueError(f"{path} is missing columns: {', '.join(sorted(missing))}")
        try:
            return min(rows, key=lambda row: float(row["aic"]))
        except ValueError as error:
            raise ValueError(f"{path} contains no fit rows") from error


def main():
    args = parse_args()
    best = read_best_fit(args.fit)
    vine_id = int(best["vine_id"])

    controls = pv.FitControlsVinecop(
        family_set=pv.one_par,
        selection_criterion="aic",
        show_trace=False,
        parametric_method="mle",
    )
    trasgu = Trasgu(str(args.config))
    matrix = trasgu.get_matrix(vine_id)[0]
    data = np.loadtxt(args.data, ndmin=2)
    cop = pv.Vinecop.from_data(data, matrix=matrix, controls=controls)
    fitted_aic = cop.aic()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as output_file:
        csv.writer(output_file).writerow(
            [best["vine_id"], best["n_parameters"], best["aic"]]
        )

    with args.detailed_output.open("w", encoding="utf-8") as detailed_file:
        detailed_file.write(f"{matrix}\n")
        detailed_file.write(f"{cop}\n")
        detailed_file.write(f"Vine ID: {vine_id}, AIC: {fitted_aic}\n")


if __name__ == "__main__":
    main()

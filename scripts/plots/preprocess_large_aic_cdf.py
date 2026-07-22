#!/usr/bin/env python3
"""Preprocess a large AIC CSV into a compact approximate CDF."""

from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = Path("/tmp/fit_ship_wake.csv")
OUTPUT_FILE = Path("scripts/processed_aic_cdf.npz")
BINS = 50_000
CHUNK_SIZE = 2_000_000


def iter_aic(path: Path):
    """Yield finite AIC values from each CSV chunk."""
    for chunk in pd.read_csv(
        path,
        usecols=["aic"],
        dtype={"aic": "float64"},
        chunksize=CHUNK_SIZE,
    ):
        values = chunk["aic"].to_numpy(copy=False)
        yield values[np.isfinite(values)]


def find_range(path: Path) -> tuple[float, float, int]:
    """Find the AIC range and number of finite values in one pass."""
    minimum = np.inf
    maximum = -np.inf
    count = 0

    for values in iter_aic(path):
        if values.size:
            minimum = min(minimum, float(values.min()))
            maximum = max(maximum, float(values.max()))
            count += values.size

    if count == 0:
        raise ValueError("The 'aic' column contains no finite numeric values")
    return minimum, maximum, count


def preprocess(path: Path) -> tuple[np.ndarray, np.ndarray, int]:
    """Build the approximate CDF in a second pass over the CSV."""
    minimum, maximum, count = find_range(path)

    if minimum == maximum:
        return np.array([minimum]), np.array([1.0]), count

    edges = np.linspace(minimum, maximum, BINS + 1, dtype=np.float64)
    counts = np.zeros(BINS, dtype=np.int64)

    for values in iter_aic(path):
        counts += np.histogram(values, bins=edges)[0]

    cdf = np.cumsum(counts, dtype=np.int64) / count
    return edges[1:], cdf, count


def main() -> None:
    x, cdf, count = preprocess(INPUT_FILE)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUTPUT_FILE, x=x, cdf=cdf, count=np.int64(count))
    print(f"Saved to {OUTPUT_FILE} ({count:,} finite values)")


if __name__ == "__main__":
    main()

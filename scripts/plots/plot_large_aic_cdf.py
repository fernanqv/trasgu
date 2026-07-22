#!/usr/bin/env python3
"""Plot a previously processed AIC CDF and the Dissmann reference value."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


INPUT_FILE = Path("scripts/processed_aic_cdf.npz")
OUTPUT_FILE = Path("scripts/large_aic_cdf.png")
DISSMANN_AIC = -560.74


def main() -> None:
    with np.load(INPUT_FILE, allow_pickle=False) as data:
        x = data["x"]
        cdf = data["cdf"]
        count = int(data["count"])

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(9, 5))
    plt.step(x, cdf, where="post", linewidth=1)
    plt.axvline(
        DISSMANN_AIC,
        color="tab:red",
        linestyle="--",
        linewidth=1.5,
    )
    plt.annotate(
        f"Dissmann AIC = {DISSMANN_AIC:.2f}",
        xy=(DISSMANN_AIC, 0.95),
        xycoords=("data", "axes fraction"),
        xytext=(6, 0),
        textcoords="offset points",
        rotation=0,
        color="tab:red",
        ha="left",
        va="top",
    )
    plt.xlabel("AIC")
    plt.ylabel("CDF")
    plt.title("AIC CDF")
    plt.grid(True, alpha=0.4)
    plt.tight_layout()
    plt.savefig(OUTPUT_FILE, dpi=150)
    plt.close()
    print(f"Saved to {OUTPUT_FILE} ({count:,} finite values)")


if __name__ == "__main__":
    main()

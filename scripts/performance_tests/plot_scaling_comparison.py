#!/usr/bin/env python3
"""Plot pyvinecopulib thread scaling against ideal Trasgu scaling."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


THREADS = np.array([1, 2, 4, 8, 16, 20, 24, 28, 32, 36, 40, 44, 48])
PYVINECOPULIB_TIME_MS = np.array(
    [
        176.9,
        105.0,
        77.0,
        54.7,
        39.0,
        39.0,
        39.2,
        41.5,
        42.2,
        45.3,
        46.4,
        50.6,
        52.5,
    ]
)
X_TICKS = np.arange(0, 49, 8)
Y_TICKS = np.array([1, 2, 4, 8, 16, 32, 48])

OUTPUT_DIR = Path("scripts/performance_tests")
OUTPUT_STEM = "vine_scaling_comparison"


def main() -> None:
    pyvine_speedup = PYVINECOPULIB_TIME_MS[0] / PYVINECOPULIB_TIME_MS
    trasgu_speedup = THREADS.astype(float)  # Assumed perfect scaling.

    pyvine_efficiency = pyvine_speedup / THREADS
    trasgu_efficiency = trasgu_speedup / THREADS

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.size": 10,
            "axes.labelsize": 11,
            "axes.titlesize": 12,
            "legend.fontsize": 9,
        }
    )

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    blue = "#0072B2"
    orange = "#D55E00"
    ax = axes[0]

    ax.plot(
        THREADS,
        pyvine_speedup,
        marker="o",
        markersize=6,
        linewidth=2,
        color=blue,
        label="pyvinecopulib threads",
        zorder=3,
    )
    ax.plot(
        THREADS,
        trasgu_speedup,
        marker="s",
        markersize=5,
        linewidth=2,
        color=orange,
        label="Trasgu workers",
        zorder=2,
    )
    ax.set_yscale("log", base=2)
    ax.set_xlim(0, 50)
    ax.set_xticks(X_TICKS)
    ax.set_yticks(Y_TICKS, labels=Y_TICKS)
    ax.set_xlabel("Allocated CPUs")
    ax.set_ylabel(r"Speedup $S(p)=T(1)/T(p)$")
    ax.set_title("(a) Scaling")
    ax.grid(True, which="major", linestyle=":", alpha=0.45)
    ax.legend(loc="upper left", frameon=False)

    ax = axes[1]
    ax.plot(
        THREADS,
        pyvine_efficiency,
        marker="o",
        markersize=6,
        linewidth=2,
        color=blue,
        label="pyvinecopulib threads",
    )
    ax.plot(
        THREADS,
        trasgu_efficiency,
        marker="s",
        markersize=5,
        linewidth=2,
        color=orange,
        label="Trasgu workers",
    )
    ax.set_xlim(0, 50)
    ax.set_xticks(X_TICKS)
    ax.set_ylim(0, 1.07)
    ax.set_xlabel("Allocated CPUs")
    ax.set_ylabel(r"Parallel efficiency $E(p)=S(p)/p$")
    ax.set_title("(b) Parallel efficiency")
    ax.grid(True, which="major", linestyle=":", alpha=0.45)
    ax.legend(loc="lower left", frameon=False)

    fig.suptitle("Scaling of 8-dimensional vine copula fitting", y=1.02)
    fig.tight_layout()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "pdf", "svg"):
        output = OUTPUT_DIR / f"{OUTPUT_STEM}.{extension}"
        fig.savefig(output, dpi=300, bbox_inches="tight")
        print(f"Saved {output}")


if __name__ == "__main__":
    main()

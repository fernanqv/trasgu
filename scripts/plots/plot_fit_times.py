#!/usr/bin/env python3
"""Plot fitting time and fitted-matrix counts by number of variables."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


N_VARS = [4, 5, 6, 7, 8]
TIME_MINUTES = [0.01, 0.42, 31, 4898, 1810202]
MATRICES_FITTED = [12, 480, 23040, 2580480, 660602880]
TIME_LABELS = ["< 1 second", "27 s", "31 min", "3.4 days", "3.4 years"]


def compact_number(value: float, _position: int) -> str:
    for divisor, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if value >= divisor:
            return f"{value / divisor:g}{suffix}"
    return f"{value:g}"


def main() -> None:
    output = Path(__file__).with_name("fit_times_bar_chart.png")
    fig, time_axis = plt.subplots(figsize=(11, 6))
    matrix_axis = time_axis.twinx()
    width = 0.36
    time_positions = [value - width / 2 for value in N_VARS]
    matrix_positions = [value + width / 2 for value in N_VARS]

    time_bars = time_axis.bar(
        time_positions, TIME_MINUTES, width=width, color="#3978b5", label="Fitting time"
    )
    matrix_bars = matrix_axis.bar(
        matrix_positions,
        MATRICES_FITTED,
        width=width,
        color="#e07a2d",
        label="Matrices fitted",
    )

    time_axis.set_xlabel("Number of variables")
    time_axis.set_ylabel("Time (minutes)", color="#3978b5")
    matrix_axis.set_ylabel("Number of matrices", color="#e07a2d")
    time_axis.set_xticks(N_VARS)
    time_axis.set_yscale("log")
    matrix_axis.set_yscale("log")
    matrix_axis.yaxis.set_major_formatter(FuncFormatter(compact_number))
    time_axis.tick_params(axis="y", colors="#3978b5")
    matrix_axis.tick_params(axis="y", colors="#e07a2d")
    time_axis.grid(axis="y", which="both", alpha=0.2)
    time_axis.set_axisbelow(True)

    for bar, label in zip(time_bars, TIME_LABELS):
        time_axis.annotate(
            label,
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(-3, 4), textcoords="offset points", ha="right", fontsize=8,
            color="#285783",
        )
    for bar, value in zip(matrix_bars, MATRICES_FITTED):
        matrix_axis.annotate(
            f"{value:,}",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(3, 4), textcoords="offset points", ha="left", fontsize=8,
            color="#9c511d",
        )

    handles = [time_bars, matrix_bars]
    time_axis.legend(handles, [item.get_label() for item in handles], loc="upper left")
    fig.suptitle("Vine fitting workload by dimensionality", fontsize=15, weight="bold")
    fig.tight_layout()
    fig.savefig(output, dpi=200, bbox_inches="tight")
    print(output)


if __name__ == "__main__":
    main()

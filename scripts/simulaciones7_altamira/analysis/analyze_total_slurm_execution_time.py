#!/usr/bin/env python3
"""Sum effective trasgu_run time across chunks and plot it by sample size."""

from __future__ import annotations

import argparse
import csv
import re
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt


STAMP = r"(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
START = re.compile(rf"^{STAMP} .* Parallel fitting chunk (?P<chunk>\d+) .* using \d+ workers$")
END = re.compile(rf"^{STAMP} .* Results saved to .*/fit_chunk_(?P<chunk>\d+)_\d+\.csv$")


def parse_chunk(path: Path) -> tuple[int, int]:
    start = end = chunk = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = START.match(line)
        if match:
            start = datetime.fromisoformat(match["time"])
            chunk = int(match["chunk"])
            continue
        match = END.match(line)
        if match:
            end = datetime.fromisoformat(match["time"])
            if chunk is not None and int(match["chunk"]) != chunk:
                raise ValueError(f"Chunk mismatch in {path}")
    if start is None or end is None or chunk is None:
        raise ValueError(f"Incomplete timing in {path}")
    return chunk, int((end - start).total_seconds())


def collect(root: Path, iteration: int) -> list[dict[str, object]]:
    rows = []
    size_dirs = sorted(
        (path for path in root.iterdir() if path.is_dir() and path.name.isdigit()),
        key=lambda path: int(path.name),
    )
    for size_dir in size_dirs:
        pattern = (
            f"simulations/iteration_{iteration}/.snakemake/"
            "slurm_logs/rule_fit_chunk/*/*.log"
        )
        completed = {}
        for path in sorted(size_dir.glob(pattern)):
            try:
                chunk, seconds = parse_chunk(path)
            except ValueError:
                continue
            if chunk in completed:
                raise ValueError(f"Duplicate completed chunk {chunk} in {size_dir}")
            completed[chunk] = seconds
        if not completed:
            continue
        total = sum(completed.values())
        rows.append({
            "sample_size": int(size_dir.name),
            "iteration": iteration,
            "completed_chunks": len(completed),
            "total_trasgu_run_seconds": total,
            "total_trasgu_run_minutes": total / 60,
            "total_trasgu_run_hours": total / 3600,
        })
    return rows


def read_csv(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def plot(rows: list[dict[str, object]], path: Path) -> None:
    x = [int(row["sample_size"]) for row in rows]
    y = [float(row["total_trasgu_run_hours"]) for row in rows]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(x, y, color="#4C78A8", marker="o", linewidth=2.2, markersize=7)
    for size, hours in zip(x, y):
        ax.annotate(f"{hours:.2f} h", (size, hours), xytext=(0, 8),
                    textcoords="offset points", ha="center", fontsize=8)
    ax.set(title="Summed trasgu_run time across all chunks",
           xlabel="Sample size", ylabel="Summed trasgu_run time (hours)")
    ax.set_xticks(x)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main() -> None:
    analysis_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=analysis_dir.parent)
    parser.add_argument("--iteration", type=int, default=1)
    parser.add_argument(
        "--from-csv", action="store_true",
        help="Regenerate the plot from the saved summary when raw logs are unavailable.",
    )
    args = parser.parse_args()
    csv_path = analysis_dir / "total_execution_times.csv"
    if args.from_csv:
        rows = read_csv(csv_path)
    else:
        rows = collect(args.root, args.iteration)
        if not rows:
            raise SystemExit("No complete fit_chunk logs found; use --from-csv to plot saved totals")
        write_csv(rows, csv_path)
    plot(rows, analysis_dir / "total_execution_time.png")
    print(f"Plotted {len(rows)} sample sizes.")


if __name__ == "__main__":
    main()

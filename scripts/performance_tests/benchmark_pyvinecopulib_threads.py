#!/usr/bin/env python3
"""Simple benchmark of num_threads in pyvinecopulib."""

from __future__ import annotations

import random
import statistics
import time

import numpy as np
import pyvinecopulib as pv


# ---------------------------------------------------------------------------
# CONFIGURATION: modify only this section.
# ---------------------------------------------------------------------------
DATA_FILE = "scripts/performance_tests/input8_300_gumbel_high.txt"

# Use None to select every column. Example for the first eight: slice(0, 8).
COLUMNS = slice(0, 8)

THREADS = [1, 2, 4, 8, 16, 20, 24, 28, 32, 36, 40, 44, 48]
REPETITIONS = 7
RANDOM_SEED = 42
# ---------------------------------------------------------------------------


def make_controls(num_threads: int) -> pv.FitControlsVinecop:
    """Create identical fitting controls for every measurement."""
    return pv.FitControlsVinecop(
        family_set=pv.one_par,
        parametric_method="mle",
        selection_criterion="aic",
        num_threads=num_threads,
        show_trace=False,
    )


def main() -> None:
    if not THREADS or any(t < 1 for t in THREADS):
        raise ValueError("THREADS must contain integers greater than or equal to 1")
    if REPETITIONS < 1:
        raise ValueError("REPETITIONS must be greater than or equal to 1")

    data = np.loadtxt(DATA_FILE, dtype=float, ndmin=2)
    if COLUMNS is not None:
        data = data[:, COLUMNS]
    data = np.asfortranarray(data)

    if not np.isfinite(data).all() or np.any((data <= 0.0) | (data >= 1.0)):
        raise ValueError("The data must be finite and strictly inside (0, 1)")

    print(f"pyvinecopulib: {pv.__version__}")
    print(f"Data: {DATA_FILE}")
    print(f"Observations: {data.shape[0]}; variables: {data.shape[1]}")
    print("Selecting a fixed structure (this step is not timed)...")

    initial_model = pv.Vinecop.from_data(data, controls=make_controls(1))
    matrix = np.asfortranarray(initial_model.matrix, dtype=np.uint64)

    # Randomizing the order avoids systematically favoring one configuration
    # because of cache warm-up or gradual changes in machine load.
    execution_order = THREADS * REPETITIONS
    random.Random(RANDOM_SEED).shuffle(execution_order)
    elapsed = {threads: [] for threads in THREADS}

    for run_number, threads in enumerate(execution_order, start=1):
        start = time.perf_counter()
        pv.Vinecop.from_data(
            data,
            matrix=matrix,
            controls=make_controls(threads),
        )
        duration = time.perf_counter() - start
        elapsed[threads].append(duration)
        print(
            f"Measurement {run_number:>2}/{len(execution_order)}: "
            f"{threads:>2} threads, {duration * 1000:>9.3f} ms"
        )

    medians = {
        threads: statistics.median(durations)
        for threads, durations in elapsed.items()
    }
    baseline = medians[1] if 1 in medians else medians[THREADS[0]]

    print("\nResults (medians):")
    print("| Threads | Time per fit | Speedup |")
    print("|------:|---------------:|--------:|")
    for threads in THREADS:
        milliseconds = medians[threads] * 1000
        speedup = baseline / medians[threads]
        print(f"| {threads} | {milliseconds:.1f} ms | {speedup:.2f}x |")


if __name__ == "__main__":
    main()

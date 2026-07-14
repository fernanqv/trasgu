"""Programmatic lookup of R-vine matrices in Chimera."""

from __future__ import annotations

import os.path
from collections import defaultdict
from collections.abc import Sequence
from numbers import Integral

import fsspec
import numpy as np
import pyvinecopulib as pv
import zarr

from trasgu.core import CHIMERA_TOTAL_RUNS, _is_url


DEFAULT_CHIMERA_URL = "http://meteo.unican.es/work/chimera.zarr"


def _open_store(url: str):
    if os.path.exists(url):
        return url
    if _is_url(url):
        return fsspec.filesystem("http").get_mapper(url)
    return url


def _normalize_matrix(matrix: Sequence[Sequence[int]] | np.ndarray) -> np.ndarray:
    try:
        raw = np.asarray(matrix, dtype=object)
    except (TypeError, ValueError) as error:
        raise ValueError("matrix must contain only non-negative integers") from error

    if raw.ndim != 2 or raw.shape[0] != raw.shape[1]:
        raise ValueError("matrix must be square")
    if any(
        isinstance(value, bool) or not isinstance(value, Integral) or value < 0
        for value in raw.flat
    ):
        raise ValueError("matrix must contain only non-negative integers")

    normalized = np.asarray(raw, dtype=np.uint64)
    if normalized.shape[0] not in CHIMERA_TOTAL_RUNS:
        supported = ", ".join(map(str, sorted(CHIMERA_TOTAL_RUNS)))
        raise ValueError(f"matrix dimension must be one of: {supported}")

    try:
        pv.RVineStructure.from_matrix(np.asfortranarray(normalized))
    except RuntimeError as error:
        raise ValueError(f"matrix is not a valid R-vine structure: {error}") from error

    return normalized


def find_chimera_matrix_ids(
    matrices: Sequence[Sequence[Sequence[int]] | np.ndarray],
    *,
    url: str = DEFAULT_CHIMERA_URL,
    chunk_size: int = 10_000,
) -> list[int | None]:
    """Find several Chimera IDs with one scan per matrix dimension.

    Results follow the input order. Missing matrices are represented by
    ``None``. Duplicate input matrices share the same ID.
    """
    if chunk_size < 1:
        raise ValueError("chunk_size must be at least 1")

    targets = [_normalize_matrix(matrix) for matrix in matrices]
    if not targets:
        return []

    root = zarr.open_group(_open_store(url), mode="r")
    by_dimension: dict[int, dict[bytes, list[int]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for position, target in enumerate(targets):
        contiguous = np.ascontiguousarray(target, dtype=np.uint64)
        by_dimension[target.shape[0]][contiguous.tobytes()].append(position)

    found: list[int | None] = [None] * len(targets)
    for dimension, pending in by_dimension.items():
        chimera = root[f"matrices{dimension}"]
        record_dtype = np.dtype((np.void, dimension * dimension * 8))

        for start in range(0, chimera.shape[0], chunk_size):
            stop = min(start + chunk_size, chimera.shape[0])
            chunk = np.asarray(
                chimera[start:stop, :, :], dtype=np.uint64, order="C"
            )
            records = chunk.reshape(len(chunk), -1).view(record_dtype).ravel()
            target_records = np.frombuffer(b"".join(pending), dtype=record_dtype)

            for offset in np.flatnonzero(np.isin(records, target_records)):
                positions = pending.pop(records[offset].tobytes(), [])
                for position in positions:
                    found[position] = start + int(offset)

            if not pending:
                break

    return found


def find_chimera_matrix_id(
    matrix: Sequence[Sequence[int]] | np.ndarray,
    *,
    url: str = DEFAULT_CHIMERA_URL,
    chunk_size: int = 10_000,
) -> int | None:
    """Return the zero-based Chimera ID of a matrix, or ``None`` if absent."""
    return find_chimera_matrix_ids(
        [matrix], url=url, chunk_size=chunk_size
    )[0]

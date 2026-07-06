import csv
from pathlib import Path

import numpy as np
import pytest

from trasgu import Trasgu


VALID_MATRIX_3D = np.array(
    [
        [2, 3, 3],
        [3, 2, 0],
        [1, 0, 0],
    ],
    dtype=np.uint64,
)


@pytest.fixture()
def trasgu_config(tmp_path, monkeypatch):
    data = np.array(
        [
            [0.10, 1.20, 2.10],
            [0.20, 1.10, 2.20],
            [0.30, 1.40, 2.00],
            [0.40, 1.30, 2.30],
            [0.50, 1.60, 2.40],
            [0.60, 1.50, 2.60],
            [0.70, 1.80, 2.50],
            [0.80, 1.70, 2.80],
            [0.90, 2.00, 2.70],
            [1.00, 1.90, 3.00],
        ],
        dtype=float,
    )
    data_path = tmp_path / "data.txt"
    np.savetxt(data_path, data)

    matrices = np.stack([VALID_MATRIX_3D] * 5)

    output_dir = tmp_path / "fit_results"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                f"data_file: {data_path}",
                "trasgu_url: http://example.invalid/trasgu.zarr",
                "chunk_size: 2",
                f"output_dir: {output_dir}",
                "max_workers: 1",
            ]
        )
        + "\n"
    )

    config = Trasgu(str(config_path))
    monkeypatch.setattr(
        config,
        "_load_matrices_from_zarr",
        lambda start, end: matrices[start:end],
    )
    monkeypatch.setattr(
        config,
        "get_number_of_trasgu_matrices",
        lambda: len(matrices),
    )
    return config


def read_chunk_rows(path):
    with open(path, newline="") as f:
        return list(csv.reader(f))


def test_counts_chunks_and_ranges_use_trasgu_matrices(trasgu_config):
    assert trasgu_config.get_number_of_trasgu_matrices() == 5
    assert trasgu_config.get_number_of_chunks() == 3
    assert trasgu_config.get_id_chunk_from_matrix_id(4) == 2
    assert trasgu_config.print_chunk_matrices_range(1) == (2, 3)


def test_measure_fitting_time_returns_minutes(trasgu_config):
    elapsed_minutes = trasgu_config.measure_fitting_time()

    assert elapsed_minutes >= 0


def test_fit_vinecop_chunk_to_file_writes_expected_rows(trasgu_config):
    results = trasgu_config.fit_vinecop_chunk_to_file(chunk_index=1)

    assert results.shape == (2, 3)
    np.testing.assert_array_equal(results[:, 0], [2, 3])

    output_path = (
        Path(trasgu_config.output_dir)
        / f"fit_chunk_{1:04d}_{trasgu_config.chunk_size:05d}.csv"
    )
    rows = read_chunk_rows(output_path)

    assert len(rows) == 2
    assert [int(rows[0][0]), int(rows[1][0])] == [2, 3]
    assert all(len(row) == 3 for row in rows)


def test_chunk_status_reports_finished_and_missing_chunks(trasgu_config):
    trasgu_config.fit_vinecop_chunk_to_file(chunk_index=0)

    status = trasgu_config.get_chunk_status()

    assert status["total_chunks"] == 3
    assert status["finished_chunks"] == [0]
    assert status["finished_chunks_count"] == 1
    assert status["missing_chunks"] == [1, 2]
    assert status["completion_percentage"] == pytest.approx(100 / 3)


def test_combine_chunks_adds_header_and_can_delete_chunks(trasgu_config):
    trasgu_config.fit_vinecop_chunk_to_file(chunk_index=0)
    trasgu_config.fit_vinecop_chunk_to_file(chunk_index=1)

    combined_path = trasgu_config.combine_chunks(
        output_filename="combined_test.csv",
        delete_chunks=True,
    )

    rows = read_chunk_rows(combined_path)
    assert rows[0] == ["vine_id", "n_parameters", "aic"]
    assert [int(row[0]) for row in rows[1:]] == [0, 1, 2, 3]
    assert not list(Path(trasgu_config.output_dir).glob("fit_chunk_*.csv"))


def test_fit_all_chunks_can_limit_and_combine_at_end(trasgu_config):
    trasgu_config.fit_all_chunks(
        skip_finished=False,
        max_chunks=2,
        combine_at_end=True,
    )

    output_dir = Path(trasgu_config.output_dir)
    combined_path = output_dir / "final_results.csv"
    rows = read_chunk_rows(combined_path)

    assert rows[0] == ["vine_id", "n_parameters", "aic"]
    assert [int(row[0]) for row in rows[1:]] == [0, 1, 2, 3]
    assert (output_dir / "fit_chunk_0000_00002.csv").exists()
    assert (output_dir / "fit_chunk_0001_00002.csv").exists()

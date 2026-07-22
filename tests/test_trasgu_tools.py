import csv
from pathlib import Path

import numpy as np
import pytest
import yaml

import trasgu
from trasgu import CHIMERA_TOTAL_RUNS, Trasgu

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
            [0.10, 0.20, 0.21],
            [0.20, 0.10, 0.22],
            [0.30, 0.40, 0.20],
            [0.40, 0.30, 0.23],
            [0.50, 0.60, 0.24],
            [0.60, 0.50, 0.26],
            [0.70, 0.80, 0.25],
            [0.80, 0.70, 0.28],
            [0.90, 0.95, 0.27],
            [0.95, 0.90, 0.30],
        ],
        dtype=float,
    )
    data_path = tmp_path / "data.txt"
    np.savetxt(data_path, data)

    matrices = np.stack([VALID_MATRIX_3D] * 5)

    output_dir = tmp_path / "fit_results"
    config_path = tmp_path / "trasgu.yaml"
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


def make_config(tmp_path, data):
    data_path = tmp_path / "data.txt"
    np.savetxt(data_path, data)

    return make_config_for_data_file(tmp_path, data_path)


def make_config_for_data_file(tmp_path, data_path, columns=None):
    lines = [
        f"data_file: {data_path}",
        "trasgu_url: http://example.invalid/trasgu.zarr",
        "chunk_size: 2",
        f"output_dir: {tmp_path / 'fit_results'}",
    ]
    if columns is not None:
        lines.append(f"columns: {columns}")

    config_path = tmp_path / "trasgu.yaml"
    config_path.write_text("\n".join(lines) + "\n")
    return Trasgu(str(config_path))


@pytest.mark.parametrize(
    ("suffix", "delimiter"),
    [
        (".csv", ","),
        (".tsv", "\t"),
    ],
)
def test_loads_delimited_text_data_files(tmp_path, suffix, delimiter):
    data = np.array(
        [
            [0.1, 0.2, 0.3, 0.4],
            [0.2, 0.3, 0.4, 0.5],
            [0.3, 0.4, 0.5, 0.6],
        ]
    )
    data_path = tmp_path / f"data{suffix}"
    np.savetxt(data_path, data, delimiter=delimiter)

    config = make_config_for_data_file(tmp_path, data_path)

    assert config.n_vars == 4
    np.testing.assert_allclose(config.data, data)


def test_loads_npy_data_files(tmp_path):
    data = np.array(
        [
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [0.2, 0.3, 0.4, 0.5, 0.6],
            [0.3, 0.4, 0.5, 0.6, 0.7],
        ]
    )
    data_path = tmp_path / "data.npy"
    np.save(data_path, data)

    config = make_config_for_data_file(tmp_path, data_path)

    assert config.n_vars == 5
    np.testing.assert_allclose(config.data, data)


@pytest.mark.parametrize(
    "invalid_value",
    [0.0, 1.0, -0.1, 1.1, np.nan, np.inf],
)
def test_rejects_values_that_are_not_pseudo_observations(tmp_path, invalid_value):
    data = np.full((3, 4), 0.5)
    data[1, 2] = invalid_value
    config = make_config(tmp_path, data)

    with pytest.raises(ValueError, match="pseudo-observations.*between 0 and 1"):
        config.data


def test_rejects_non_matrix_data_files(tmp_path):
    data_path = tmp_path / "data.npy"
    np.save(data_path, np.array([0.1, 0.2, 0.3]))

    with pytest.raises(ValueError, match="2D numerical matrix"):
        make_config_for_data_file(tmp_path, data_path)


def test_rejects_data_files_with_more_than_eight_variables(tmp_path):
    data_path = tmp_path / "data.txt"
    np.savetxt(data_path, np.ones((3, 9)))

    with pytest.raises(ValueError, match="supports at most 8"):
        make_config_for_data_file(tmp_path, data_path)


def test_selects_configured_columns_with_one_based_indices(tmp_path):
    data = (np.arange(30, dtype=float).reshape(3, 10) + 1) / 31
    data_path = tmp_path / "data.csv"
    np.savetxt(data_path, data, delimiter=",")

    config = make_config_for_data_file(tmp_path, data_path, columns=[1, 3, 5, 7])

    assert config.n_vars == 4
    np.testing.assert_array_equal(config.data, data[:, [0, 2, 4, 6]])


def test_selects_configured_columns_in_user_order(tmp_path):
    data = (np.arange(30, dtype=float).reshape(3, 10) + 1) / 31
    data_path = tmp_path / "data.npy"
    np.save(data_path, data)

    config = make_config_for_data_file(tmp_path, data_path, columns=[7, 5, 3, 1])

    assert config.n_vars == 4
    np.testing.assert_array_equal(config.data, data[:, [6, 4, 2, 0]])


def test_rejects_duplicate_columns(tmp_path):
    data_path = tmp_path / "data.txt"
    np.savetxt(data_path, np.ones((3, 6)))

    with pytest.raises(ValueError, match="duplicate"):
        make_config_for_data_file(tmp_path, data_path, columns=[1, 3, 3, 5])


def test_rejects_out_of_range_columns(tmp_path):
    data_path = tmp_path / "data.txt"
    np.savetxt(data_path, np.ones((3, 6)))

    with pytest.raises(ValueError, match="out of range"):
        make_config_for_data_file(tmp_path, data_path, columns=[1, 3, 7])


def test_number_of_trasgu_matrices_uses_static_chimera_counts(tmp_path):
    config = make_config(tmp_path, np.ones((3, 6)))

    assert config.get_number_of_trasgu_matrices() == CHIMERA_TOTAL_RUNS[6]


def test_default_config_uses_trasgu_yaml_and_run_relative_paths(tmp_path, monkeypatch):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    data_path = run_dir / "data.txt"
    np.savetxt(data_path, np.ones((3, 6)))
    (run_dir / "trasgu.yaml").write_text(
        "\n".join(
            [
                "data_file: data.txt",
                "chunk_size: 2",
            ]
        )
        + "\n"
    )

    monkeypatch.chdir(run_dir)
    config = Trasgu()

    assert config.data_file == str(data_path)
    assert config.config_name == "run"
    assert config.output_dir == str(run_dir / ".trasgu_run")
    assert config.final_results_path == run_dir / "fit_run.csv"
    assert config.get_number_of_trasgu_matrices() == CHIMERA_TOTAL_RUNS[6]


def test_output_dir_is_optional_and_run_relative(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    data_path = run_dir / "data.txt"
    np.savetxt(data_path, np.ones((3, 6)))
    config_path = run_dir / "trasgu.yaml"
    config_path.write_text(
        "\n".join(
            [
                "data_file: data.txt",
                "chunk_size: 2",
                "output_dir: outputs",
            ]
        )
        + "\n"
    )

    config = Trasgu(str(config_path))

    assert config.output_dir == str(run_dir / "outputs")


def test_number_of_trasgu_matrices_can_verify_against_zarr(tmp_path, monkeypatch):
    class FakeMatrices:
        shape = (5, 3, 3)

    config = make_config(tmp_path, np.ones((3, 3)))
    monkeypatch.setattr(
        trasgu.core.zarr,
        "open_group",
        lambda store, mode: {"matrices3": FakeMatrices()},
    )

    assert config.get_number_of_trasgu_matrices(use_zarr=True) == 5


def test_static_number_of_trasgu_matrices_rejects_unknown_sizes(tmp_path):
    config = make_config(tmp_path, np.ones((3, 3)))

    with pytest.raises(ValueError, match="No static Chimera matrix count"):
        config.get_number_of_trasgu_matrices()


def test_counts_chunks_and_ranges_use_trasgu_matrices(trasgu_config):
    assert trasgu_config.get_number_of_trasgu_matrices() == 5
    assert trasgu_config.get_number_of_chunks() == 3
    assert trasgu_config.get_id_chunk_from_matrix_id(4) == 2
    assert trasgu_config.print_chunk_matrices_range(1) == (2, 3)


def test_measure_fitting_time_returns_minutes(trasgu_config):
    elapsed_minutes = trasgu_config.measure_fitting_time()

    assert elapsed_minutes >= 0


def test_measure_fitting_time_uses_available_matrix_count(trasgu_config, monkeypatch):
    loaded_ranges = []
    monkeypatch.setattr(trasgu_config, "get_number_of_trasgu_matrices", lambda: 5)
    original_loader = trasgu_config._load_matrices_from_zarr
    monkeypatch.setattr(
        trasgu_config,
        "_load_matrices_from_zarr",
        lambda start, end: (
            loaded_ranges.append((start, end)),
            original_loader(start, end),
        )[1],
    )

    trasgu_config.measure_fitting_time()

    assert loaded_ranges == [(0, 5)]


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


def test_fit_given_matrix_returns_detailed_serializable_fit(trasgu_config):
    result = trasgu_config.fit_given_matrix(3)

    assert result["matrix_id"] == 3
    assert result["n_variables"] == 3
    assert result["n_observations"] == len(trasgu_config.data)
    assert isinstance(result["aic"], float)
    assert isinstance(result["bic"], float)
    assert isinstance(result["loglik"], float)
    assert len(result["bicopulas"]) == 3
    assert set(result["bicopulas"][0]) == {
        "tree",
        "edge",
        "family",
        "rotation",
        "parameters",
        "tau",
    }
    yaml.safe_dump(result)


def test_chunk_fit_uses_input_pseudo_observations_unchanged(trasgu_config, monkeypatch):
    received = None

    def capture_data(matrices, data, base_vine_id):
        nonlocal received
        received = data
        return np.empty((len(matrices), 3))

    monkeypatch.setattr(trasgu_config, "_fit_vinecop_chunk_internal", capture_data)

    trasgu_config.fit_vinecop_chunk_parallel(0)

    assert received is trasgu_config.data


def test_fit_given_matrix_rejects_out_of_range_id(trasgu_config):
    with pytest.raises(ValueError, match="between 0 and 4"):
        trasgu_config.fit_given_matrix(5)


def test_get_best_fits_returns_lowest_aic_in_order(trasgu_config, monkeypatch):
    rows = [
        (3, 3, -10.0),
        (1, 3, -30.0),
        (4, 3, 2.0),
        (2, 3, -30.0),
        (0, 3, -20.0),
    ]
    with trasgu_config.final_results_path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["vine_id", "n_parameters", "aic"])
        writer.writerows(rows)

    fitted = []

    def fake_fit(matrix_id):
        fitted.append(matrix_id)
        return {"matrix_id": matrix_id, "aic": float(matrix_id)}

    monkeypatch.setattr(trasgu_config, "fit_given_matrix", fake_fit)

    results = trasgu_config.get_best_fits(3)

    assert fitted == [1, 2, 0]
    assert [result["source_aic"] for result in results] == [-30.0, -30.0, -20.0]
    assert [result["rank"] for result in results] == [1, 2, 3]


def test_get_best_fits_returns_all_rows_when_count_is_larger(
    trasgu_config, monkeypatch
):
    trasgu_config.final_results_path.write_text(
        "vine_id,n_parameters,aic\n3,3,-1.0\n1,3,-2.0\n"
    )
    monkeypatch.setattr(
        trasgu_config,
        "fit_given_matrix",
        lambda matrix_id: {"matrix_id": matrix_id},
    )

    results = trasgu_config.get_best_fits(10)

    assert [result["matrix_id"] for result in results] == [1, 3]


@pytest.mark.parametrize("count", [0, -1])
def test_get_best_fits_rejects_non_positive_count(trasgu_config, count):
    with pytest.raises(ValueError, match="greater than 0"):
        trasgu_config.get_best_fits(count)


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
    combined_path = trasgu_config.final_results_path
    rows = read_chunk_rows(combined_path)

    assert rows[0] == ["vine_id", "n_parameters", "aic"]
    assert [int(row[0]) for row in rows[1:]] == [0, 1, 2, 3]
    assert (output_dir / "fit_chunk_0000_00002.csv").exists()
    assert (output_dir / "fit_chunk_0001_00002.csv").exists()

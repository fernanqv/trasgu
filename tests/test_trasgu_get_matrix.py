import sys

import numpy as np

from trasgu.cli import get_matrix as trasgu_get_matrix


def _mock_get_matrix(monkeypatch):
    opened_stores = []
    requested_arrays = []

    class MockGroup:
        def __getitem__(self, name):
            requested_arrays.append(name)
            data = np.arange(36).reshape(1, 6, 6)
            return data

    def mock_open_group(store, mode):
        opened_stores.append(store)
        return MockGroup()

    monkeypatch.setattr(trasgu_get_matrix.zarr, "open_group", mock_open_group)
    return opened_stores, requested_arrays


def test_trasgu_get_matrix_uses_cli_variable_count_without_yaml(
    tmp_path, monkeypatch, capsys
):
    opened_stores, requested_arrays = _mock_get_matrix(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "trasgu_get_matrix",
            "6",
            "0",
            "--url",
            "/scratch/user/chimera.zarr",
        ],
    )

    trasgu_get_matrix.main()

    output = capsys.readouterr().out
    assert "Variables: 6" in output
    assert "Matrix ID: 0" in output
    assert opened_stores == ["/scratch/user/chimera.zarr"]
    assert requested_arrays == ["matrices6"]


def test_trasgu_get_matrix_can_print_copyable_numpy_expression(
    tmp_path, monkeypatch, capsys
):
    _mock_get_matrix(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "trasgu_get_matrix",
            "6",
            "0",
            "--url",
            "/scratch/user/chimera.zarr",
            "--numpy",
        ],
    )

    trasgu_get_matrix.main()

    assert capsys.readouterr().out == (
        "np.array([[0, 1, 2, 3, 4, 5], "
        "[6, 7, 8, 9, 10, 11], "
        "[12, 13, 14, 15, 16, 17], "
        "[18, 19, 20, 21, 22, 23], "
        "[24, 25, 26, 27, 28, 29], "
        "[30, 31, 32, 33, 34, 35]])\n"
    )

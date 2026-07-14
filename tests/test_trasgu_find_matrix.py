import sys

import numpy as np
import yaml

from trasgu.cli import find_matrix as trasgu_find_matrix


MATRIX = [
    [4, 4, 4, 4],
    [3, 3, 3, 0],
    [2, 2, 0, 0],
    [1, 0, 0, 0],
]


def test_finds_matrix_id_from_yaml_in_chunks(tmp_path, monkeypatch, capsys):
    yaml_path = tmp_path / "dissmann_1.yaml"
    yaml_path.write_text(yaml.safe_dump({"aic": -12.5, "matrix": MATRIX}))

    other = np.zeros((4, 4), dtype=np.uint64)
    stored = np.stack([other, other, MATRIX, other])

    class MockGroup:
        def __getitem__(self, name):
            assert name == "matrices4"
            return stored

    monkeypatch.setattr(
        trasgu_find_matrix.zarr,
        "open_group",
        lambda store, mode: MockGroup(),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "trasgu_find_matrix",
            str(yaml_path),
            "--url",
            "/local/chimera.zarr",
            "--chunk-size",
            "2",
        ],
    )

    trasgu_find_matrix.main()

    assert capsys.readouterr().out == "2\n"


def test_rejects_yaml_without_matrix(tmp_path, monkeypatch, capsys):
    yaml_path = tmp_path / "missing.yaml"
    yaml_path.write_text(yaml.safe_dump({"aic": -12.5}))
    monkeypatch.setattr(sys, "argv", ["trasgu_find_matrix", str(yaml_path)])

    try:
        trasgu_find_matrix.main()
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("trasgu_find_matrix should fail")

    assert "top-level 'matrix' key" in capsys.readouterr().err

import sys

import pytest

from trasgu.cli import examples as trasgu_examples


def test_trasgu_examples_lists_available_examples(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["trasgu_examples", "--list"])

    trasgu_examples.main()

    output = capsys.readouterr().out
    assert "minimal" in output
    assert "parallel_debug" in output
    assert "profiles" in output
    assert "all" in output


def test_trasgu_examples_copies_self_contained_minimal_example(tmp_path, monkeypatch):
    destination = tmp_path / "minimal"
    monkeypatch.setattr(
        sys,
        "argv",
        ["trasgu_examples", "minimal", str(destination)],
    )

    trasgu_examples.main()

    config = destination / "trasgu.yaml"
    data = destination / "input6_500_gumbel_high.txt"
    assert config.exists()
    assert data.exists()
    assert "data_file: input6_500_gumbel_high.txt" in config.read_text()


def test_trasgu_examples_refuses_to_overwrite_without_force(tmp_path, monkeypatch):
    destination = tmp_path / "minimal"
    destination.mkdir()
    config = destination / "trasgu.yaml"
    config.write_text("local changes")

    monkeypatch.setattr(
        sys,
        "argv",
        ["trasgu_examples", "minimal", str(destination)],
    )

    with pytest.raises(SystemExit) as exc_info:
        trasgu_examples.main()

    assert exc_info.value.code == 1
    assert config.read_text() == "local changes"

import importlib
import sys
import tomllib
from pathlib import Path

import pytest


CLI_MODULES = [
    ("trasgu_combine", "trasgu.cli.combine", True),
    ("trasgu_monitor", "trasgu.cli.monitor", True),
    ("trasgu_fit_chunk", "trasgu.cli.fit_chunk", True),
    ("trasgu_fit_given_matrix", "trasgu.cli.fit_given_matrix", True),
    ("trasgu_count_chunks", "trasgu.cli.count_chunks", True),
    ("trasgu_time_fit", "trasgu.cli.time_fit", True),
    ("trasgu_get_matrix", "trasgu.cli.get_matrix", False),
    ("trasgu_find_matrix", "trasgu.cli.find_matrix", False),
    ("trasgu_run", "trasgu.cli.run", True),
    ("trasgu_download_zarr", "trasgu.cli.download_zarr", False),
    ("trasgu_examples", "trasgu.cli.examples", False),
]


@pytest.mark.parametrize(("command", "module_name", "uses_run_dir"), CLI_MODULES)
def test_cli_help_exits_successfully(command, module_name, uses_run_dir, monkeypatch, capsys):
    module = importlib.import_module(module_name)
    monkeypatch.setattr(sys, "argv", [command, "--help"])

    with pytest.raises(SystemExit) as exc_info:
        module.main()

    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert "usage:" in output
    assert "Examples:" in output
    if uses_run_dir:
        assert "trasgu.yaml" in output


def test_documented_cli_modules_match_project_scripts():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())
    scripts = pyproject["project"]["scripts"]

    expected = {command: module for command, module, _ in CLI_MODULES}
    actual = {command: target.split(":", maxsplit=1)[0] for command, target in scripts.items()}

    assert actual == expected

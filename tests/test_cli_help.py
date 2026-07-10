import importlib
import sys
import tomllib
from pathlib import Path

import pytest


CLI_MODULES = [
    ("trasgu_combine", "scripts.trasgu_combine", True),
    ("trasgu_monitor", "scripts.trasgu_monitor", True),
    ("trasgu_fit_chunk", "scripts.trasgu_fit_chunk", True),
    ("trasgu_count_chunks", "scripts.trasgu_count_chunks", True),
    ("trasgu_time_fit", "scripts.trasgu_time_fit", True),
    ("trasgu_get_matrix", "scripts.trasgu_get_matrix", False),
    ("trasgu_run", "scripts.trasgu_run", True),
    ("trasgu_download_zarr", "scripts.trasgu_download_zarr", False),
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

import subprocess
import tomllib
import sys
from pathlib import Path

import numpy as np

from scripts import trasgu_run


def make_run_dir(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    np.savetxt(run_dir / "data.txt", np.ones((3, 6)))
    (run_dir / "trasgu.yaml").write_text(
        "\n".join(
            [
                "data_file: data.txt",
                "chunk_size: 1000",
                "output_dir: fit_results",
                "max_workers: 3",
            ]
        )
        + "\n"
    )
    return run_dir


def test_trasgu_run_uses_max_workers_as_local_cores(tmp_path, monkeypatch):
    run_dir = make_run_dir(tmp_path)
    calls = []

    def fake_run(cmd, check, env):
        calls.append((cmd, env))
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.chdir(run_dir)
    monkeypatch.setattr(sys, "argv", ["trasgu_run"])
    monkeypatch.setattr(trasgu_run.subprocess, "run", fake_run)

    trasgu_run.main()

    cmd, env = calls[0]
    assert Path(cmd[0]).stem == "snakemake"
    assert cmd[1] == "--snakefile"
    assert Path(cmd[2]).name == "Snakefile"
    assert cmd[3:5] == ["--cores", "3"]
    assert env["XDG_CACHE_HOME"] == str(run_dir / ".snakemake" / "cache")


def test_trasgu_run_resolves_packaged_slurm_profile(tmp_path, monkeypatch):
    run_dir = make_run_dir(tmp_path)
    calls = []

    def fake_run(cmd, check, env):
        calls.append((cmd, env))
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.chdir(run_dir)
    monkeypatch.setattr(sys, "argv", ["trasgu_run", "--profile", "slurm"])
    monkeypatch.setattr(trasgu_run.subprocess, "run", fake_run)

    trasgu_run.main()

    cmd, _ = calls[0]
    assert "--cores" not in cmd
    assert Path(cmd[0]).stem == "snakemake"
    assert cmd[1] == "--snakefile"
    assert cmd[3] == "--profile"
    assert Path(cmd[4]).parts[-2:] == ("profiles", "slurm")


def test_trasgu_run_passes_extra_snakemake_args(tmp_path, monkeypatch):
    run_dir = make_run_dir(tmp_path)
    calls = []

    def fake_run(cmd, check, env):
        calls.append((cmd, env))
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.chdir(run_dir)
    monkeypatch.setattr(sys, "argv", ["trasgu_run", "--dry-run", "--printshellcmds"])
    monkeypatch.setattr(trasgu_run.subprocess, "run", fake_run)

    trasgu_run.main()

    cmd, _ = calls[0]
    assert "--dry-run" in cmd
    assert "--printshellcmds" in cmd


def test_slurm_executor_is_optional_dependency():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())

    dependencies = pyproject["project"]["dependencies"]
    slurm_extra = pyproject["project"]["optional-dependencies"]["slurm"]

    assert "snakemake-executor-plugin-slurm>=0.10" not in dependencies
    assert slurm_extra == ["snakemake-executor-plugin-slurm>=0.10"]
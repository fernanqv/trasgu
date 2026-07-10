#!/usr/bin/env python3
from importlib import resources
import os
from pathlib import Path
import subprocess
import sys

from trasgu.cli._shared import parser as make_parser
from trasgu.cli._shared import run_directory_error


def _workflow_path(name: str) -> Path:
    return Path(str(resources.files("trasgu.workflow").joinpath(name)))


def _profile_path(profile: str) -> Path:
    if profile == "slurm":
        return _workflow_path("profiles/slurm")
    return Path(profile).expanduser().resolve()


def _snakemake_executable() -> str:
    scripts_dir = Path(sys.executable).parent
    for executable in ("snakemake", "snakemake.exe"):
        candidate = scripts_dir / executable
        if candidate.exists():
            return str(candidate)
    return "snakemake"


def _prepare_run_env() -> dict[str, str]:
    env = os.environ.copy()
    run_cache = Path.cwd() / ".snakemake" / "cache"
    run_cache.mkdir(parents=True, exist_ok=True)
    env.setdefault("XDG_CACHE_HOME", str(run_cache))
    os.environ.setdefault("XDG_CACHE_HOME", env["XDG_CACHE_HOME"])

    mpl_cache = Path.cwd() / ".snakemake" / "matplotlib"
    mpl_cache.mkdir(parents=True, exist_ok=True)
    env.setdefault("MPLCONFIGDIR", str(mpl_cache))
    os.environ.setdefault("MPLCONFIGDIR", env["MPLCONFIGDIR"])
    return env


def _patch_slurm_jobstep_plugin():
    try:
        import snakemake_executor_plugin_slurm_jobstep
        plugin_file = Path(snakemake_executor_plugin_slurm_jobstep.__file__)
        if plugin_file.exists():
            content = plugin_file.read_text()
            if "SLURM_CONF" not in content and '"SLURM_SUBMIT_HOST",' in content:
                patched = content.replace(
                    '"SLURM_SUBMIT_HOST",',
                    '"SLURM_SUBMIT_HOST",\n            "SLURM_CONF",'
                )
                plugin_file.write_text(patched)
    except Exception:
        pass


def main():
    _patch_slurm_jobstep_plugin()
    parser = make_parser(
        "Run the packaged Snakemake workflow for a trasgu run directory.",
        """
        Examples:
          trasgu_examples minimal ./minimal
          cd minimal
          trasgu_run --dry-run
          trasgu_run
          trasgu_run --profile slurm
          trasgu_run --profile /path/to/snakemake-profile --printshellcmds
          trasgu_run --unlock

        Notes:
          Run from a directory containing trasgu.yaml.
          Local runs use max_workers from trasgu.yaml as the Snakemake --cores value.
          Use --profile slurm for the packaged SLURM profile.
          Extra arguments are passed through to Snakemake.
        """,
    )
    parser.add_argument(
        "--profile",
        help="Snakemake profile to use. Use 'slurm' for the packaged SLURM profile.",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show the Snakemake plan without running jobs.",
    )
    parser.add_argument(
        "--unlock",
        action="store_true",
        help="Unlock the Snakemake working directory.",
    )

    args, snakemake_args = parser.parse_known_args()

    try:
        env = _prepare_run_env()
        from trasgu import Trasgu

        config = Trasgu()
        snakefile = _workflow_path("Snakefile")

        cmd = [_snakemake_executable(), "--snakefile", str(snakefile)]
        if args.profile:
            cmd.extend(["--profile", str(_profile_path(args.profile))])
        else:
            cmd.extend(["--cores", str(config.max_workers)])

        if "SLURM_CONF" in env:
            has_envvars = any(
                arg == "--envvars" or arg.startswith("--envvars=")
                for arg in snakemake_args
            )
            if not has_envvars:
                cmd.extend(["--envvars", "SLURM_CONF"])

        if args.dry_run:
            cmd.append("--dry-run")
        if args.unlock:
            cmd.append("--unlock")

        cmd.extend(snakemake_args)

        subprocess.run(cmd, check=True, env=env)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except Exception as e:
        print(f"Error: {run_directory_error(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

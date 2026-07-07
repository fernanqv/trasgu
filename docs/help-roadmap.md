# Help roadmap

This roadmap describes the documentation work for `trasgu`.

## Goals

- Make the first successful local run obvious.
- Make every CLI command explain its inputs, outputs, and working directory.
- Document every supported `trasgu.yaml` field.
- Cover local, SLURM, and offline-Zarr workflows.
- Keep documentation close to code and protected by tests.

## Implemented foundation

- Rich `--help` output for public CLI commands.
- MkDocs navigation under `docs/`.
- Dedicated pages for installation, configuration, CLI usage, workflows, HPC, offline Zarr, outputs, examples, troubleshooting, and development.
- Basic CLI help tests.

## Next improvements

- Add a JSON Schema for `trasgu.yaml`.
- Generate the CLI reference from live `--help` output.
- Add screenshots or terminal recordings for the minimal workflow.
- Expand troubleshooting with real cluster failures as they appear.
- Publish versioned documentation when releases become regular.

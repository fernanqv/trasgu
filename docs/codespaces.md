# GitHub Codespaces

GitHub Codespaces is the easiest way to try `trasgu` without installing anything locally.

The repository includes a Dev Container configuration. When the Codespace starts, it:

- uses Python 3.12,
- installs `uv`,
- creates the project `.venv`,
- synchronizes dependencies from `uv.lock`,
- configures VS Code to use the virtual environment.

## Start a Codespace

From the GitHub repository page:

1. Click **Code**.
2. Open the **Codespaces** tab.
3. Click **Create codespace on main**.
4. Wait until the setup command finishes.

## Run the minimal example

```bash
cd examples/run_config/minimal
trasgu_run --dry-run
```

To run the workflow for real:

```bash
trasgu_run
```

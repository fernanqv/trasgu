# Chimera Vines

`trasgu` is a high-performance toolkit for fitting **Vine Copulas** using structured matrices from the **Chimera** project. It is designed to handle massive quantities of vine structures by distributing the workload into manageable "chunks," supporting both local multi-core execution and high-performance computing (HPC) clusters via SLURM.

---

## 🚀 Key Features

-   **High Performance**: Leverages `pyvinecopulib` for efficient C++-backed copula fitting.
-   **Structured Exploration**: Specifically designed to work with Chimera Zarr structures.
-   **Scalable**: Efficiently splits millions of vine structures into chunks for parallel processing.
-   **HPC Ready**: Built-in support for SLURM array jobs with customizable launcher templates.
-   **CLI-First**: Comprehensive suite of command-line tools for a streamlined workflow.

---

## 🛠 Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/geoocean/trasgu.git
    cd trasgu
    ```

2.  Install the locked runtime environment with `uv`:
    ```bash
    uv sync --frozen --no-dev
    ```

3.  Either run commands through `uv`:
    ```bash
    cd examples/run_config/minimal
    uv run --project ../../.. --frozen trasgu_run --dry-run
    ```

    or activate the project environment for an interactive session:
    ```bash
    source .venv/bin/activate
    cd examples/run_config/minimal
    trasgu_run --dry-run
    ```

For development tools, install the default development group:
```bash
uv sync --frozen
```

If `uv` is not installed yet, install it first:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Alternatively, install in editable mode with `pip`:
```bash
pip install -e .
```

---

## 🧩 Chunk-based Processing

To handle the millions of potential vine structures efficiently, `trasgu` uses a **chunk-based processing** strategy. Instead of loading and fitting every structure at once, the work is divided into smaller groups called "chunks."

### How it works:
1.  **Segmentation**: The total number of vine structures (e.g., 600M+) is divided by your defined `chunk_size` (e.g., 20,000).
2.  **Parallelization**:
    -   **Local**: Within a single chunk, fitting is distributed across `max_workers` CPU cores.
    -   **HPC (SLURM)**: Each chunk is submitted as an independent task in a SLURM job array, allowing thousands of chunks to be processed simultaneously across a cluster.
3.  **Persistence**: Each chunk saves its results to a unique CSV file (`fit_chunk_NNNN_MMMMM.csv`). This prevents data loss if a long-running task is interrupted.
4.  **Aggregation**: Once all chunks are finished, they are combined into a single `final_results.csv` for analysis.

This approach ensures **low memory footprint**, **fault tolerance**, and **massive scalability**.

---

## ⚙️ Run Configuration

Each run is configured by a `trasgu.yaml` file in the directory where commands are executed. Relative paths inside `trasgu.yaml` are resolved from that directory; absolute paths are used as-is.

For example:

```bash
cd examples/run_config/minimal
trasgu_count_chunks
trasgu_time_fit
trasgu_run
```

Below are the available `trasgu.yaml` parameters:

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `data_file` | String | **Yes** | Path to the `.txt` numerical data matrix (observations in rows, variables in columns). |
| `chunk_size` | Integer | **Yes** | Number of vine copulas to process per chunk (e.g., 20,000). |
| `output_dir` | String | **Yes** | Directory where CSV results will be saved. |
| `max_workers` | Integer | No | Number of CPU cores to use for local processing (Default: 1). |
| `controls_file` | String | No | Path to a pickled `pyvinecopulib.FitControlsVinecop` object. |
| `trasgu_url` | String | No | Local path or URL to the Chimera Zarr database. |

### Example `trasgu.yaml`
```yaml
data_file: ../../inputs/input6_500_gumbel_high.txt
chunk_size: 2000
output_dir: fit_results
max_workers: 4
controls_file: ../../controls/controls.pkl
```

---

## 🐍 Snakemake Workflow

`trasgu_run` is the recommended way to execute a full run. It launches the packaged Snakemake workflow from the current run directory, where `trasgu.yaml` lives.

Local execution:

```bash
cd examples/run_config/minimal
trasgu_run
```

The value of `max_workers` in `trasgu.yaml` is used as the Snakemake `threads` value for each chunk. For local runs, `trasgu_run` also sets `--cores max_workers`, so only one chunk runs at a time. To use more cores locally, increase `max_workers`.

Dry run:

```bash
trasgu_run --dry-run
```

SLURM execution with the packaged profile:

```bash
cd examples/run_config/altamira
trasgu_run --profile slurm
```

Custom Snakemake profile:

```bash
trasgu_run --profile /path/to/snakemake-profile
```

Additional unknown arguments are passed through to Snakemake:

```bash
trasgu_run --dry-run --printshellcmds
```

The workflow generates all expected chunk CSV files and then combines them into `final_results.csv`.

---

## 🧰 CLI Toolkit

The package provides several command-line entry points:

### 1. `trasgu_run`
Run the full Snakemake workflow from the current run directory.
```bash
[geocean02 minimal]$ trasgu_run
```

### 2. `trasgu_time_fit`
Estimate how long it will take to process your data.
```bash
[geocean02 minimal]$ trasgu_time_fit
2026-01-20 19:02:58 - vine_config - INFO - Estimated time for full chunk (1000) running with 1 workers: 1.64 minutes
```

### 3. `trasgu_count_chunks`
Return the number of chunks for the desired configuration

```bash
[geocean02 minimal]$ trasgu_count_chunks
24
```

### 4. `trasgu_monitor`
Check the progress and completion percentage of your fitting task.
```bash
valvanuz@login01:> trasgu_monitor
2026-01-20 19:07:16 - vine_config - INFO - Status: 130/130 chunks finished (100.00%)

--- Processing Status ---
Total Chunks:   130
Finished:       130
Completion:     100.00%
All chunks finished!
-------------------------
```

### 4. `trasgu_combine`
Finalize the task by merging all chunk CSVs into a single master file.
```bash
valvanuz@login01:> trasgu_combine
2026-01-20 19:08:09 - vine_config - INFO - Status: 130/130 chunks finished (100.00%)
2026-01-20 19:08:09 - vine_config - INFO - Combining 130 chunks into fit_results_altamira/final_results.csv
2026-01-20 19:08:10 - vine_config - INFO - Combined file saved to fit_results_altamira/final_results.csv
Successfully combined chunks into: fit_results_altamira/final_results.csv
valvanuz@login01:> head fit_results_altamira/final_results.csv 
vine_id,n_parameters,aic
0,21,-9304.195685
1,21,-9323.297687
2,21,-9269.211495
3,21,-9145.024796
4,21,-9168.838010
5,21,-9280.147407
6,21,-9230.251631
7,21,-9029.644844
8,21,-8808.064343
```

### 5. `trasgu_fit_chunk`
Manually fit a specific chunk. Used internally by Snakemake but available for debugging.
```bash
trasgu_fit_chunk 0  # Process chunk index 0
```

### Deprecated commands
`trasgu_fit_all` and `trasgu_submit_slurm` are deprecated. Use `trasgu_run` locally and `trasgu_run --profile slurm` on SLURM.

---

## 🔄 Recommended Workflow

1.  **Preparation**: Create a run directory with `trasgu.yaml` and prepare your data file.
2.  **Estimation**: Run `trasgu_time_fit` to determine the optimal `chunk_size` and expected duration.
3.  **Execution**: Run `trasgu_run` locally, or `trasgu_run --profile slurm` on a cluster.
4.  **Monitoring**: Use `trasgu_monitor` periodically to see how many chunks are finished.
5.  **Aggregation**: Snakemake runs `trasgu_combine` automatically after all chunks are complete.

---

## 📂 SLURM Integration

SLURM execution is handled through Snakemake profiles. The packaged `slurm` profile is available through:

```bash
trasgu_run --profile slurm
```

The `Snakefile` reads `max_workers` from `trasgu.yaml` and uses it as `threads` for each chunk. The SLURM executor maps those threads to the CPUs requested for each chunk job.

---

## 🧪 Advanced: Custom Fitting Controls

If you need specific fitting logic (e.g., custom family sets or selection criteria), create a Python script to pickle a `FitControlsVinecop` object:

```python
import pyvinecopulib as pv
import pickle

controls = pv.FitControlsVinecop(
    family_set=[pv.BicopFamily.gaussian, pv.BicopFamily.t],
    selection_criterion="bic"
)

with open("my_controls.pkl", "wb") as f:
    pickle.dump(controls, f)
```
Then reference it in your `trasgu.yaml`, relative to the run directory: `controls_file: ../../controls/my_controls.pkl`.

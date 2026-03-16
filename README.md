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

2.  Install in editable mode:
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

## ⚙️ Configuration (YAML)

All tools in this toolkit rely on a YAML configuration file. Below are the available parameters:

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `data_file` | String | **Yes** | Path to the `.txt` numerical data matrix (observations in rows, variables in columns). |
| `chunk_size` | Integer | **Yes** | Number of vine copulas to process per chunk (e.g., 20,000). |
| `output_dir` | String | **Yes** | Directory where CSV results will be saved. |
| `slurm_launcher` | String | **Yes*** | Path to your SLURM bash script template. *Required only for SLURM tools.* |
| `max_workers` | Integer | No | Number of CPU cores to use for local processing (Default: 1). |
| `controls_file` | String | No | Path to a pickled `pyvinecopulib.FitControlsVinecop` object. |
| `trasgu_url` | String | No | Local path or URL to the Chimera Zarr database. |

### Example `config.yaml`
```yaml
data_file: examples/inputs/input6_500_gumbel_high.txt
chunk_size: 2000
output_dir: fit_results
slurm_launcher: examples/launchers/launch_geoocean.sh
max_workers: 4
controls_file: examples/controls/controls.pkl
```

---

## 🧰 CLI Toolkit

The package provides several command-line entry points:

### 1. `trasgu_time_fit`
Estimate how long it will take to process your data.
```bash
[geocean02 trasgu]$ trasgu_time_fit examples/run_config/minimal.yaml 
2026-01-20 19:02:58 - vine_config - INFO - Estimated time for full chunk (1000) running with 1 workers: 1.64 minutes
```
### 2. `trasgu_count_chunks`
Return the number of chunks for the desired configuration

```bash
[geocean02 trasgu]$ trasgu_count_chunks examples/run_config/minimal.yaml 
24
```

### 3. `trasgu_submit_slurm`
Submit missing chunks as a SLURM array job to your cluster.
```bash
valvanuz@login01:> trasgu_submit_slurm examples/run_config/altamira.yaml 
2026-01-20 18:49:41 - vine_config - INFO - Status: 0/130 chunks finished (0.00%)
2026-01-20 18:49:41 - vine_config - INFO - Launching SLURM array job: sbatch --array=0-129 --ntasks=4 --nodes=1 examples/launchers/launch_altamira.sh examples/run_config/altamira.yaml
2026-01-20 18:49:41 - vine_config - INFO - SLURM output: Submitted batch job 699021
```

### 4. `trasgu_monitor`
Check the progress and completion percentage of your fitting task.
```bash
valvanuz@login01:> trasgu_monitor examples/run_config/altamira.yaml 
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
valvanuz@login01:> trasgu_combine examples/run_config/altamira.yaml 
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
Manually fit a specific chunk. Used internally by SLURM but available for debugging.
```bash
trasgu_fit_chunk config.yaml 0  # Process chunk index 0
```

### 6. `trasgu_fit_all`
Fit all chunks sequentially on your local machine.
```bash
trasgu_fit_all config.yaml
```

---

## 🔄 Recommended Workflow

1.  **Preparation**: Create your `config.yaml` and prepare your data file.
2.  **Estimation**: Run `trasgu_time_fit` to determine the optimal `chunk_size` and expected duration.
3.  **Submission**: If using a cluster, run `trasgu_submit_slurm`.
4.  **Monitoring**: Use `trasgu_monitor` periodically to see how many chunks are finished.
5.  **Aggregation**: Once 100% complete, run `trasgu_combine` to generate your final result file.

---

## 📂 SLURM Integration

To use SLURM, you must provide a launcher script (defined in your YAML as `slurm_launcher`). This script acts as a template for the array job.

**Example `launch_geoocean.sh`:**
```bash
#!/bin/bash
#SBATCH --job-name="trasgu"
#SBATCH --partition=priority
#SBATCH --nodes=1

# The toolkit will automatically append the chunk index as the last argument
trasgu_fit_chunk --config $1 $SLURM_ARRAY_TASK_ID
```

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
Then reference it in your YAML: `controls_file: examples/controls/my_controls.pkl`.

# Usage Guide: vine_config.py

## What is vine_config.py?

`vine_config.py` is a tool for fitting vine copulas using predefined structures from Chimera and input data. It allows processing large quantities of vine structures by dividing the work into "chunks" (fragments).

## Initial Configuration

### 1. Create a YAML configuration file

Create a YAML file (e.g., `my_config.yaml`) with the following parameters:

```yaml
data_file: inputs/input7_500_gauss_high.txt  # Path to the input data file
chunk_size: 27000                             # Number of vines per chunk
output_dir: fit_results                       # Directory where results will be saved
```

**Optional parameters:**
- `chimera_url`: URL of the Chimera Zarr file (default: `https://geoocean.sci.unican.es/chimera/chimera.zarr`)

### Understanding the YAML Configuration File

The YAML configuration file is a text file that stores all the settings required to run `vine_config.py`. Here's a detailed explanation of each parameter:

**Required parameters:**

- **`data_file`**: Path to your input data file (relative or absolute)
  - Must be a `.txt` file containing a numerical matrix
  - Example: `inputs/input7_500_gauss_high.txt`

- **`chunk_size`**: Number of vine copulas to process in each chunk
  - Larger values process more vines per chunk but require more memory
  - Recommended range: 100-27000 depending on available RAM
  - Start with 100 for testing and increase based on your hardware capacity

- **`output_dir`**: Directory where the CSV results will be saved
  - Will be created if it doesn't exist
  - Example: `fit_results`

**Optional parameters:**

- **`chimera_url`**: URL or path to the Chimera Zarr database
  - Default: `https://geoocean.sci.unican.es/chimera/chimera.zarr`
  - Use this to override the default Chimera source if needed

- **`controls_file`**: Path to a pickle file containing custom `FitControlsVinecop` settings
  - If not provided, default controls are used with: family_set=`pv.one_par`, selection_criterion=`aic`, parametric_method=`mle`
  - Use this to apply custom fitting parameters (e.g., different family sets, selection criteria, or estimation methods)
  - Example: `controls_file: custom_controls.pkl`
  - To create a custom controls file, use pyvinecopulib to configure and pickle the FitControlsVinecop object

**Example configuration files:**

Simple configuration for testing:
```yaml
data_file: inputs/input7_500_gauss_high.txt
chunk_size: 100
output_dir: test_results
```

Production configuration with custom Chimera source:
```yaml
data_file: inputs/input7_500_gauss_high.txt
chunk_size: 27000
output_dir: fit_results
chimera_url: https://geoocean.sci.unican.es/chimera/chimera.zarr
```

Advanced configuration with custom fitting controls:
```yaml
data_file: inputs/input7_500_gauss_high.txt
chunk_size: 27000
output_dir: fit_results
controls_file: custom_controls.pkl
```

### 2. Prepare data file

Your data file should be a `.txt` with a matrix where:
- Each row = an observation
- Each column = a variable
- Values separated by spaces or tabs

Example: `inputs/input7_500_gauss_high.txt` with 7 variables and 500 observations

## Basic Usage

### Import and load configuration

```python
from vine_config import ChimeraVines

# Load configuration from YAML
config = ChimeraVines("my_config.yaml")
```

### Main Methods

#### 1. **Estimate processing time**
Before processing all chunks, estimate how long it will take:

```python
estimated_time = config.measure_fitting_time()
# Prints: "Estimated time for full chunk (27000): X.XX minutes"
```

This method fits 100 test vines and projects the time for a full chunk.

#### 2. **Fit a chunk and save results**
Process a specific chunk and save the results to CSV:

```python
config.fit_vinecop_chunk_to_file(chunk_index=0)
# Saves: fit_results/fit_chunk_0000_27000.csv
```

The CSV file contains:
- `vine_id`: Vine identifier
- `n_parameters`: Number of parameters of the fitted model
- `aic`: Akaike Information Criterion

#### 3. **Get information about chunks**

```python
# Total number of matrices available in Chimera
total_matrices = config.get_number_of_chimera_matrices()

# Number of chunks needed
n_chunks = config.get_number_of_chunks()

# Which chunk contains a specific matrix?
chunk_id = config.get_id_chunk_from_matrix_id(15000)
```

#### 4. **Monitor progress**
Check which chunks have already been processed:

```python
progress = config.monitor_fitting_progress()
# Returns: {0: 27000, 1: 27000, 2: 15000, ...}
# Where the key is the chunk_index and the value is the number of vines processed
```

#### 5. **Access data and matrices**

```python
# Load input data
data = config.get_data_from_file()

# Load a specific matrix from Chimera
matrix = config.get_matrix_from_id(100)

# Load a range of matrices
matrices = config.load_matrices_from_zarr(start=0, end=100)
```

## Recommended Workflow

### Step 1: Minimal configuration for testing
Create `test.yaml`:
```yaml
data_file: inputs/input7_500_gauss_high.txt
chunk_size: 100
output_dir: test_results
```

### Step 2: Estimate time
```python
config = ChimeraVines("test.yaml")
config.measure_fitting_time()
```

### Step 3: Process a test chunk
```python
config.fit_vinecop_chunk_to_file(chunk_index=0)
```

### Step 4: Adjust chunk_size and scale
Based on the estimated time, adjust `chunk_size` in your YAML for production:
```yaml
chunk_size: 27000  # Optimal size based on your resources
```

### Step 5: Process all chunks
```python
config = ChimeraVines("production.yaml")
n_chunks = config.get_number_of_chunks()

for chunk_id in range(n_chunks):
    config.fit_vinecop_chunk_to_file(chunk_id)
    print(f"Completed chunk {chunk_id}/{n_chunks}")
```

## Parallel Processing (experimental)

The `fit_vinecop_chunk_parallel()` method is available but requires adjustments according to your needs:

```python
config.fit_vinecop_chunk_parallel()
```

Note: This method currently processes 8 chunks in parallel with 8 workers. Customize based on your hardware.

## Output file structure

Results are saved in CSV format:
```
fit_results/
├── fit_chunk_0000_27000.csv
├── fit_chunk_0001_27000.csv
├── fit_chunk_0002_27000.csv
└── ...
```

CSV format:
```
vine_id,n_parameters,aic
0,21,1234.567890
1,18,1156.234567
...
```

## Advanced Configuration

Vine copula fitting uses these default parameters:
- `family_set`: Families with one parameter (`pv.one_par`)
- `selection_criterion`: AIC (Akaike Information Criterion)
- `parametric_method`: MLE (Maximum Likelihood Estimation)

To modify these parameters, edit the `_fit_vinecop_chunk_internal()` method in `vine_config.py`.

## Troubleshooting

- **Error "Data file not found"**: Verify that the path in `data_file` is correct
- **Excessive time**: Reduce `chunk_size` for smaller chunks
- **Insufficient memory**: Reduce `chunk_size` or process fewer vines per chunk

---

## Summary of available methods

| Method | Description |
|--------|-------------|
| `measure_fitting_time()` | Estimates the processing time for a full chunk |
| `fit_vinecop_chunk_to_file(chunk_index)` | Fits a chunk and saves results to CSV |
| `fit_vinecop_chunk(chunk_index)` | Fits a chunk and returns results (without saving) |
| `get_number_of_chimera_matrices()` | Gets the total number of available matrices |
| `get_number_of_chunks()` | Calculates the number of chunks needed |
| `load_matrices_from_zarr(start, end)` | Loads a range of matrices from Chimera |
| `get_matrix_from_id(matrix_id)` | Gets a specific matrix by ID |
| `get_data_from_file()` | Loads the input data |
| `get_id_chunk_from_matrix_id(matrix_id)` | Gets the chunk containing a matrix |
| `monitor_fitting_progress()` | Shows the progress of processed chunks |
| `fit_vinecop_chunk_parallel()` | Processes multiple chunks in parallel (experimental) |

---

Do you need help with any specific aspect of using `vine_config.py`?

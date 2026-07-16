# Usage:
# First minimal.yaml with a single line:
# input_data: inputs/input7_500_gauss_high.txt
# Use measure_fitting_time to estimate time for full chunk
# Then modify chunk_size in minimal.yaml and run fit_vinecop_chunk_to_file to fit and save results for chunk 0

import yaml
import zarr
import fsspec
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Tuple, Any
import pyvinecopulib as pv
import os.path
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import glob
import re
import pickle
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("vine_config")
logger.debug("Debug message")

CHIMERA_TOTAL_RUNS = {
    4: 12,
    5: 480,
    6: 23040,
    7: 2580480,
    8: 660602880,
}

DEFAULT_CONFIG_NAME = "trasgu.yaml"
MAX_SUPPORTED_VARS = max(CHIMERA_TOTAL_RUNS)


def _is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"}


def _data_file_delimiter(path: str | Path) -> str | None:
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return ","
    if suffix == ".tsv":
        return "\t"
    return None


def _ensure_data_matrix(data: np.ndarray, path: str | Path) -> np.ndarray:
    if data.ndim != 2:
        raise ValueError(f"Data file {path} must contain a 2D numerical matrix.")
    if data.shape[0] == 0 or data.shape[1] == 0:
        raise ValueError(f"Data file {path} contains no data rows.")
    return data


def _ensure_pseudo_observations(
    data: np.ndarray, path: str | Path
) -> np.ndarray:
    if not np.all(np.isfinite(data)):
        raise ValueError(
            f"Data file {path} must contain finite pseudo-observations "
            "strictly between 0 and 1."
        )
    if np.any((data <= 0) | (data >= 1)):
        raise ValueError(
            f"Data file {path} must contain pseudo-observations strictly "
            "between 0 and 1."
        )
    return data


def _normalize_columns(
    columns: list[int] | tuple[int, ...] | None, n_columns: int
) -> np.ndarray | None:
    if columns is None:
        return None
    if not isinstance(columns, (list, tuple)):
        raise ValueError("columns must be a list of 1-based column indices.")
    if not columns:
        raise ValueError("columns must contain at least one column index.")

    selected = []
    for column in columns:
        if isinstance(column, bool) or not isinstance(column, int):
            raise ValueError("columns must contain only 1-based integer indices.")
        if column < 1:
            raise ValueError("columns must contain 1-based indices greater than 0.")
        if column > n_columns:
            raise ValueError(
                f"Column {column} is out of range for data with {n_columns} columns."
            )
        selected.append(column)

    if len(set(selected)) != len(selected):
        raise ValueError("columns must not contain duplicate indices.")

    return np.array([column - 1 for column in selected], dtype=int)


def _ensure_supported_n_vars(n_vars: int, path: str | Path, has_columns: bool) -> int:
    if n_vars <= MAX_SUPPORTED_VARS:
        return n_vars

    if not has_columns:
        raise ValueError(
            f"Data file {path} has {n_vars} variables, but Trasgu supports at most "
            f"{MAX_SUPPORTED_VARS}. Set columns in trasgu.yaml to choose a subset."
        )
    raise ValueError(
        f"Trasgu supports at most {MAX_SUPPORTED_VARS} variables; got {n_vars}."
    )


def _select_columns(
    data: np.ndarray, columns: list[int] | tuple[int, ...] | None, path: str | Path
) -> np.ndarray:
    data = _ensure_data_matrix(data, path)
    selected = _normalize_columns(columns, data.shape[1])
    if selected is None:
        return data
    return data[:, selected]


class Trasgu:
    """
    Configuration for vine copula analysis from YAML.
    Loads YAML parameters as class attributes and provides
    methods to access Chimera data.
    """

    def __init__(self, yaml_path: str = DEFAULT_CONFIG_NAME):
        """
        Initialize configuration from a YAML file.

        Args:
            yaml_path: Path to the YAML configuration file.
        """
        logger.debug(f"Initializing Trasgu with YAML file: {yaml_path}")
        self.yaml_path = Path(yaml_path)
        self.config_dir = self.yaml_path.resolve().parent
        self.config_name = (
            self.config_dir.name
            if self.yaml_path.stem == Path(DEFAULT_CONFIG_NAME).stem
            else self.yaml_path.stem
        )

        # Load YAML
        with open(self.yaml_path, "r") as f:
            config = yaml.safe_load(f)

        # Assign all YAML parameters as attributes
        for key, value in config.items():
            if not key.startswith("#"):  # Ignore comments
                setattr(self, key, value)

        for path_attr in ("data_file", "output_dir", "controls_file"):
            if hasattr(self, path_attr):
                setattr(
                    self,
                    path_attr,
                    str(self._resolve_run_path(getattr(self, path_attr))),
                )

        if hasattr(self, "debug") and self.debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled via configuration")

        if not hasattr(self, "trasgu_url"):
            fs = fsspec.filesystem("http")
            self.trasgu_store = fs.get_mapper(
                "http://meteo.unican.es/work/chimera.zarr"
            )
        else:
            # If .trasgu_url is a local path, use local filesystem, else use HTTP
            if not _is_url(self.trasgu_url):
                self.trasgu_url = str(self._resolve_run_path(self.trasgu_url))

            if os.path.exists(self.trasgu_url):
                self.trasgu_store = self.trasgu_url
            else:
                fs = fsspec.filesystem("http")
                self.trasgu_store = fs.get_mapper(self.trasgu_url)

        if not hasattr(self, "output_dir"):
            self.output_dir = str(self.config_dir / f".trasgu_{self.config_name}")
        self.final_results_path = self.config_dir / f"fit_{self.config_name}.csv"

        if not hasattr(self, "chunk_size"):
            self.chunk_size = 30000

        if not hasattr(self, "max_workers"):
            self.max_workers = 1
        else:
            if self.max_workers <= 0:
                raise ValueError("max_workers must be greater than 0")
            self.max_workers = int(self.max_workers)

        if not hasattr(self, "controls_file"):
            logger.debug("Using default controls")
            self.controls = pv.FitControlsVinecop(
                family_set=pv.one_par,
                selection_criterion="aic",
                show_trace=False,
                parametric_method="mle",
            )
        else:
            logger.debug("Loading controls pickle")
            with open(self.controls_file, "rb") as f:
                self.controls = pickle.load(f)

        self._data = None
        self.n_vars = self._get_n_vars_from_file()

    def _resolve_run_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return self.config_dir / path

    def _resolve_combined_output_path(
        self, output_filename: Optional[str | Path]
    ) -> Path:
        if output_filename is None:
            return self.final_results_path
        return self._resolve_run_path(output_filename)

    def __repr__(self) -> str:
        """Human-readable representation of the configuration."""
        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        return f"Trasgu({attrs})"

    def _fit_vinecop_chunk_internal(
        self,
        matrices: np.ndarray,
        data: np.ndarray,
        base_vine_id: int,
    ) -> np.ndarray:
        """
        Fit vine copulas for a chunk of matrices and calculate AIC.

        Args:
            matrices: Array of structure matrices to fit.
            data: The data to fit the copulas to.
            base_vine_id: The starting index for the matrices in this chunk.

        Returns:
            Numpy array of results, each row containing [vine_id, npars, aic].
        """
        logger.debug(
            f"Fitting chunk of {len(matrices)} matrices starting at ID {base_vine_id}"
        )
        results = []

        for offset, matrix in enumerate(matrices):
            vine_id = base_vine_id + offset

            cop = pv.Vinecop.from_data(data, matrix=matrix, controls=self.controls)
            aic = cop.aic()
            results.append((int(vine_id), int(cop.npars), aic))

        results_array = np.array(results)
        if results_array.size > 0:
            results_array[:, :2] = results_array[:, :2].astype(int)

        logger.debug(f"Completed fitting chunk starting at ID {base_vine_id}")
        return results_array

    def _load_matrices_from_zarr(self, start: int, end: int) -> np.ndarray:
        """
        Load matrices from Chimera Zarr.

        Args:
            start: Starting index (inclusive).
            end: Ending index (exclusive).

        Returns:
            Numpy array of shape (end-start, n_vars, n_vars).
        """
        logger.debug(f"Loading matrices from {start} to {end}")
        root = zarr.open_group(self.trasgu_store, mode="r")
        matrices = root[f"matrices{self.n_vars}"]
        data = matrices[start:end, :, :]
        return np.array(data)

    def get_matrix(self, matrix_id: int) -> np.ndarray:
        """
        Get a single matrix by ID.

        Args:
            matrix_id: Index of the matrix.

        Returns:
            Numpy array of shape (1, n_vars, n_vars).
        """
        matrix = self._load_matrices_from_zarr(matrix_id, matrix_id + 1)
        logger.debug(f"Loaded matrix {matrix_id}")
        return matrix

    def fit_given_matrix(self, matrix_id: int) -> Dict[str, Any]:
        """Fit one Chimera matrix and return detailed, serializable fit data."""
        total_matrices = self.get_number_of_trasgu_matrices()
        if isinstance(matrix_id, bool) or not isinstance(matrix_id, int):
            raise TypeError("matrix_id must be an integer")
        if matrix_id < 0 or matrix_id >= total_matrices:
            raise ValueError(
                f"matrix_id must be between 0 and {total_matrices - 1} "
                f"for {self.n_vars} variables"
            )

        matrix = self.get_matrix(matrix_id)[0]
        cop = pv.Vinecop.from_data(
            self.data,
            matrix=matrix,
            controls=self.controls,
        )

        pair_copulas = []
        for tree in range(cop.trunc_lvl):
            for edge in range(cop.dim - tree - 1):
                bicop = cop.get_pair_copula(tree, edge)
                family = str(bicop.family)
                if "." in family:
                    family = family.rsplit(".", 1)[-1]
                pair_copulas.append(
                    {
                        "tree": tree + 1,
                        "edge": edge + 1,
                        "family": family,
                        "rotation": int(bicop.rotation),
                        "parameters": np.asarray(bicop.parameters).tolist(),
                        "tau": float(bicop.tau),
                    }
                )

        return {
            "matrix_id": matrix_id,
            "n_variables": int(cop.dim),
            "n_observations": int(cop.nobs),
            "n_parameters": float(cop.npars),
            "loglik": float(cop.loglik()),
            "aic": float(cop.aic()),
            "bic": float(cop.bic()),
            "matrix": np.asarray(cop.matrix).tolist(),
            "bicopulas": pair_copulas,
        }

    def _get_data_from_file(self) -> np.ndarray:
        """
        Load data from the input file specified in config.

        Returns:
            Numpy array with the data.
        """
        logger.debug(f"Loading data from {self.data_file}")
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Data file not found: {self.data_file}")
        data_path = Path(self.data_file)
        if data_path.suffix.lower() == ".npy":
            data = np.load(data_path)
        else:
            data = np.loadtxt(data_path, delimiter=_data_file_delimiter(data_path))
        data = _select_columns(
            np.asarray(data), getattr(self, "columns", None), self.data_file
        )
        data = _ensure_pseudo_observations(data, self.data_file)
        _ensure_supported_n_vars(
            data.shape[1], self.data_file, hasattr(self, "columns")
        )
        return data

    @property
    def data(self) -> np.ndarray:
        if self._data is None:
            self._data = self._get_data_from_file()
        return self._data

    def _get_n_vars_from_file(self) -> int:
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Data file not found: {self.data_file}")
        data_path = Path(self.data_file)
        columns = getattr(self, "columns", None)
        if data_path.suffix.lower() == ".npy":
            data = np.load(data_path, mmap_mode="r")
            data = _ensure_data_matrix(np.asarray(data), self.data_file)
            selected = _normalize_columns(columns, data.shape[1])
            n_vars = len(selected) if selected is not None else data.shape[1]
            return _ensure_supported_n_vars(
                n_vars, self.data_file, hasattr(self, "columns")
            )

        delimiter = _data_file_delimiter(data_path)
        with open(self.data_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    n_columns = len(line.split(delimiter))
                    selected = _normalize_columns(columns, n_columns)
                    n_vars = len(selected) if selected is not None else n_columns
                    return _ensure_supported_n_vars(
                        n_vars, self.data_file, hasattr(self, "columns")
                    )
        raise ValueError(f"Data file {self.data_file} contains no data rows.")

    def get_number_of_trasgu_matrices(self, use_zarr: bool = False) -> int:
        """
        Get the total number of matrices available for the configured data size.

        Chimera is static, so the default path uses the versioned matrix counts
        for each supported number of variables. Set ``use_zarr=True`` to verify
        the value against the configured Zarr store.

        Returns:
            Total number of matrices.
        """
        if not use_zarr:
            try:
                total_matrices = CHIMERA_TOTAL_RUNS[self.n_vars]
            except KeyError as exc:
                known = ", ".join(str(n) for n in sorted(CHIMERA_TOTAL_RUNS))
                raise ValueError(
                    f"No static Chimera matrix count known for {self.n_vars} "
                    f"variables. Known values are for: {known}."
                ) from exc
            logger.debug(f"Static total number of matrices: {total_matrices}")
            return total_matrices

        root = zarr.open_group(self.trasgu_store, mode="r")
        matrices = root[f"matrices{self.n_vars}"]
        logger.debug(f"Total number of matrices: {matrices.shape[0]}")
        total_matrices = matrices.shape[0]
        return total_matrices

    def get_number_of_chunks(self, chunk_size: Optional[int] = None) -> int:
        """
        Calculate the number of chunks based on total matrices and chunk size.

        Args:
            chunk_size: Number of matrices per chunk (default from config).

        Returns:
            Number of chunks.

        """
        if chunk_size is None:
            chunk_size = self.chunk_size

        total_matrices = self.get_number_of_trasgu_matrices()
        n_chunks = (total_matrices + chunk_size - 1) // chunk_size
        logger.debug(f"Total number of chunks: {n_chunks}")
        return n_chunks

    def fit_vinecop_chunk_to_file(
        self,
        chunk_index: int,
    ) -> np.ndarray:
        """Fit vine copulas for a contiguous chunk of vine structures and save to CSV.

        This function loads pseudo-observations from `data_file` and fits a vine
        copula for each matrix loaded from the corresponding chimera zarr file.
        Results are written to a CSV in the configured chunk work directory.

        Parameters
        ----------
        chunk_index : int
            Zero-based index identifying which chunk of vines to process. The
            first vine processed is `chunk_index * chunk_size`.

        Returns
        -------
        np.ndarray
            Array of shape (chunk_size, 3) with columns
            (vine_id, n_parameters, aic).

        """
        results = self.fit_vinecop_chunk_parallel(chunk_index)

        # Save results in CSV
        output_path = os.path.join(
            self.output_dir, f"fit_chunk_{chunk_index:04d}_{self.chunk_size:05d}.csv"
        )
        np.savetxt(
            output_path,
            results,
            delimiter=",",
            fmt="%d,%d,%.6f",
            comments="",
        )
        logger.info(f"Results saved to {output_path}")
        return results

    def fit_vinecop_chunk_parallel(self, chunk_index: int) -> np.ndarray:
        """Fit vine copulas for a contiguous chunk in parallel."""
        chunk_size = self.chunk_size
        logger.info(
            f"Parallel fitting chunk {chunk_index} with size {chunk_size} using {self.max_workers} workers"
        )

        os.makedirs(self.output_dir, exist_ok=True)

        first_vine = chunk_index * chunk_size
        data = self.data

        # Load all matrices for the chunk
        logger.debug(f"Loading vines {first_vine} to {first_vine + chunk_size - 1}")
        matrices = self._load_matrices_from_zarr(first_vine, first_vine + chunk_size)

        # Split matrices into sub-chunks for each worker
        n_workers = min(self.max_workers, len(matrices))
        if n_workers == 1:
            return self._fit_vinecop_chunk_internal(matrices, data, first_vine)

        indices = np.array_split(np.arange(len(matrices)), n_workers)
        all_results = []
        with ProcessPoolExecutor(max_workers=n_workers) as ex:
            futures = []
            for idx_set in indices:
                logger.debug(f"Submitting chunk {idx_set}")
                sub_matrices = matrices[idx_set]
                base_id = first_vine + idx_set[0]
                futures.append(
                    ex.submit(
                        self._fit_vinecop_chunk_internal, sub_matrices, data, base_id
                    )
                )

            for future in as_completed(futures):
                try:
                    res = future.result()
                    all_results.append(res)
                except Exception as exc:  # noqa: BLE001
                    logger.error(f"Worker failed: {exc}")
                    raise

        # Combine and sort results by vine_id
        final_results = np.vstack(all_results)
        final_results = final_results[final_results[:, 0].argsort()]

        return final_results

    def print_chunk_matrices_range(
        self, chunk_index: int, chunk_size: Optional[int] = None
    ) -> Tuple[int, int]:
        """
        List matrices in a given chunk.

        Args:
            chunk_index: Zero-based index of the chunk.
            chunk_size: Number of matrices per chunk (default from config).
        """
        if chunk_size is None:
            chunk_size = self.chunk_size

        first_vine = chunk_index * chunk_size
        last_vine = first_vine + chunk_size - 1

        return (first_vine, last_vine)

    def measure_fitting_time(self) -> float:
        """Measure execution time for fitting a chunk of vine copulas.

        Args:
            chunk_size: Number of matrices to fit (default: 100)

        Returns:
           Time in minutes to fit a full chunk as per config.
        """
        chunk_size_short = min(100, self.get_number_of_trasgu_matrices())
        first_vine = 0
        data = self.data
        logger.debug(
            f"Loading vines {first_vine} to {first_vine + chunk_size_short - 1}"
        )
        matrices = self._load_matrices_from_zarr(
            first_vine, first_vine + chunk_size_short
        )
        logger.debug(f"Starting fit for {chunk_size_short} vine copulas...")
        start_time = time.perf_counter()
        self._fit_vinecop_chunk_internal(matrices, data, base_vine_id=0)
        elapsed_time = time.perf_counter() - start_time

        measured_matrices = len(matrices)
        time_per_chunk = elapsed_time / measured_matrices * self.chunk_size / 60
        if self.max_workers > 1:
            time_per_chunk = time_per_chunk / self.max_workers
        logger.info(
            f"Estimated time for full chunk ({self.chunk_size}) running with {self.max_workers} workers: {time_per_chunk:.2f} minutes"
        )

        return time_per_chunk

    def get_id_chunk_from_matrix_id(
        self, matrix_id: int, chunk_size: Optional[int] = None
    ) -> int:
        """
        Get the chunk index for a given matrix ID.

        Args:
            matrix_id: Index of the matrix.
            chunk_size: Number of matrices per chunk (default from config).
        """
        if chunk_size is None:
            chunk_size = self.chunk_size

        chunk_index = matrix_id // chunk_size
        logger.debug(f"Matrix ID {matrix_id} is in chunk {chunk_index}")
        return chunk_index

    def get_chunk_status(self) -> Dict[str, Any]:
        """
        Monitor the status of chunk processing.

        Returns:
            Dictionary containing:
            - total_chunks: Total number of chunks to process.
            - finished_chunks: List of indices of finished chunks.
            - missing_chunks: List of indices of missing chunks.
            - completion_percentage: Percentage of completed chunks.
        """
        total_chunks = self.get_number_of_chunks()
        finished_chunks = []

        # Find all files matching the pattern fit_chunk_NNNN_MMMMM.csv
        pattern = os.path.join(
            self.output_dir, f"fit_chunk_*_{self.chunk_size:05d}.csv"
        )
        files = glob.glob(pattern)

        for f in files:
            match = re.search(r"fit_chunk_(\d+)_", os.path.basename(f))
            if match:
                finished_chunks.append(int(match.group(1)))

        finished_chunks.sort()
        missing_chunks = [i for i in range(total_chunks) if i not in finished_chunks]

        status = {
            "total_chunks": total_chunks,
            "finished_chunks_count": len(finished_chunks),
            "finished_chunks": finished_chunks,
            "missing_chunks": missing_chunks,
            "completion_percentage": (
                (len(finished_chunks) / total_chunks * 100) if total_chunks > 0 else 0
            ),
        }

        logger.info(
            f"Status: {status['finished_chunks_count']}/{status['total_chunks']} chunks finished ({status['completion_percentage']:.2f}%)"
        )
        return status

    def combine_chunks(
        self, output_filename: Optional[str | Path] = None, delete_chunks: bool = False
    ) -> str:
        """
        Combine all chunk files into a single CSV with a header.

        Args:
            output_filename: Optional name or path of the merged output file. Relative
                paths are resolved from the run directory. If omitted, writes
                ``fit_<config>.csv`` next to the YAML file.
            delete_chunks: Whether to delete individual chunk files after merging.

        Returns:
            Path to the combined file.
        """
        status = self.get_chunk_status()
        if status["missing_chunks"]:
            logger.warning(
                f"Missing {len(status['missing_chunks'])} chunks. Merging will be incomplete."
            )

        output_path = self._resolve_combined_output_path(output_filename)
        os.makedirs(output_path.parent, exist_ok=True)

        # Sort chunks to ensure correct order
        pattern = os.path.join(
            self.output_dir, f"fit_chunk_*_{self.chunk_size:05d}.csv"
        )
        chunk_files = sorted(glob.glob(pattern))

        if not chunk_files:
            raise FileNotFoundError("No chunk files found to combine.")

        logger.info(f"Combining {len(chunk_files)} chunks into {output_path}")

        header = "vine_id,n_parameters,aic\n"
        with open(output_path, "w") as outfile:
            outfile.write(header)
            for f in chunk_files:
                with open(f, "r") as infile:
                    outfile.write(infile.read())

        if delete_chunks:
            logger.info("Deleting individual chunk files")
            for f in chunk_files:
                os.remove(f)

        logger.info(f"Combined file saved to {output_path}")
        return str(output_path)

    def fit_all_chunks(
        self,
        skip_finished: bool = True,
        max_chunks: Optional[int] = None,
        combine_at_end: bool = False,
    ) -> None:
        """
        Fit all chunks in the data series.

        Args:
            skip_finished: If True, skips chunks that already have an output file.
            max_chunks: Optional limit on the number of chunks to process.
            combine_at_end: If True, calls combine_chunks() after finishing all fits.
        """
        total_chunks = self.get_number_of_chunks()
        if max_chunks is not None:
            total_chunks = min(total_chunks, max_chunks)

        logger.info(f"Starting fitting for {total_chunks} chunks")

        status = self.get_chunk_status()
        finished_chunks = set(status["finished_chunks"])

        for i in range(total_chunks):
            if skip_finished and i in finished_chunks:
                logger.info(f"Skipping already finished chunk {i}")
                continue

            logger.info(f"Processing chunk {i+1}/{total_chunks}")
            try:
                self.fit_vinecop_chunk_to_file(i)
            except Exception as e:
                logger.error(f"Error processing chunk {i}: {e}")
                continue

        logger.info("Finished processing chunks")

        if combine_at_end:
            logger.info("Combining results at the end")
            self.combine_chunks()


if __name__ == "__main__":
    pass

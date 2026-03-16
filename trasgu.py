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
import subprocess
import itertools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("vine_config")
logger.debug("Debug message")

class Trasgu:
    """
    Configuration for vine copula analysis from YAML.
    Loads YAML parameters as class attributes and provides
    methods to access Chimera data.
    """

    def __init__(self, yaml_path: str):
        """
        Initialize configuration from a YAML file.

        Args:
            yaml_path: Path to the YAML configuration file.
        """
        logger.debug(f"Initializing Trasgu with YAML file: {yaml_path}")
        self.yaml_path = Path(yaml_path)

        # Load YAML
        with open(self.yaml_path, "r") as f:
            config = yaml.safe_load(f)

        # Assign all YAML parameters as attributes
        for key, value in config.items():
            if not key.startswith("#"):  # Ignore comments
                setattr(self, key, value)

        if hasattr(self, "debug") and self.debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled via configuration")

        if not hasattr(self, "trasgu_url"):
            fs = fsspec.filesystem("http")
            self.trasgu_store = fs.get_mapper(
                "https://geoocean.sci.unican.es/chimera/chimera.zarr"
            )
        else:
            # If .trasgu_url is a local path, use local filesystem, else use HTTP
            if os.path.exists(self.trasgu_url):
                self.trasgu_store = self.trasgu_url
            else:
                fs = fsspec.filesystem("http")
                self.trasgu_store = fs.get_mapper(self.trasgu_url)

        if not hasattr(self, "output_dir"):
            self.output_dir = "fit_results"

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

        self.data = self._get_data_from_file()
        self.n_vars = self.data.shape[1]

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

    def _get_data_from_file(self) -> np.ndarray:
        """
        Load data from the input file specified in config.

        Returns:
            Numpy array with the data.
        """
        logger.debug(f"Loading data from {self.data_file}")
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Data file not found: {self.data_file}")
        return np.loadtxt(self.data_file)

    def get_number_of_trasgu_matrices(self) -> int:
        """
        Get the total number of matrices in the Chimera Zarr file.

        Returns:
            Total number of matrices.
        """
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

        This function loads a dataset from `data_file`, converts it to pseudo-
        observations, and fits a vine copula for each matrix loaded from the
        corresponding chimera zarr file. Results are written to a CSV in
        `output_dir`.

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

    def fit_vinecop_chunk_parallel(
        self, chunk_index: int
    ) -> np.ndarray:
        """Fit vine copulas for a contiguous chunk in parallel."""
        chunk_size = self.chunk_size
        logger.info(f"Parallel fitting chunk {chunk_index} with size {chunk_size} using {self.max_workers} workers")

        os.makedirs(self.output_dir, exist_ok=True)

        # Transform data to pseudo-observations
        first_vine = chunk_index * chunk_size
        data = pv.to_pseudo_obs(self.data)
        
        # Load all matrices for the chunk
        logger.debug(f"Loading vines {first_vine} to {first_vine + chunk_size - 1}")
        matrices = self._load_matrices_from_zarr(first_vine, first_vine + chunk_size)

        # Split matrices into sub-chunks for each worker
        n_workers = min(self.max_workers, len(matrices))    
        indices = np.array_split(np.arange(len(matrices)), n_workers)
        all_results = []
        with ProcessPoolExecutor(max_workers=n_workers) as ex:
            futures = []
            for idx_set in indices:
                logger.debug(f"Submitting chunk {idx_set}")
                sub_matrices = matrices[idx_set]
                base_id = first_vine + idx_set[0]
                futures.append(ex.submit(self._fit_vinecop_chunk_internal, sub_matrices, data, base_id))

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
        last_vine = first_vine + chunk_size -1

        return((first_vine,last_vine))


    def measure_fitting_time(self) -> float:
        """Measure execution time for fitting a chunk of vine copulas.

        Args:
            chunk_size: Number of matrices to fit (default: 100)

        Returns:
           Time in minutes to fit a full chunk as per config.
        """
        chunk_size_short = 100
        first_vine = 0
        data = pv.to_pseudo_obs(self.data)
        logger.debug(f"Loading vines {first_vine} to {first_vine + chunk_size_short - 1}")
        matrices = self._load_matrices_from_zarr(
            first_vine, first_vine + chunk_size_short
        )
        logger.debug(f"Starting fit for {chunk_size_short} vine copulas...")
        start_time = time.perf_counter()
        self._fit_vinecop_chunk_internal(matrices, data, base_vine_id=0)
        elapsed_time = time.perf_counter() - start_time

        time_per_chunk = elapsed_time / chunk_size_short * self.chunk_size / 60
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
        pattern = os.path.join(self.output_dir, f"fit_chunk_*_{self.chunk_size:05d}.csv")
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
            "completion_percentage": (len(finished_chunks) / total_chunks * 100) if total_chunks > 0 else 0
        }
        
        logger.info(f"Status: {status['finished_chunks_count']}/{status['total_chunks']} chunks finished ({status['completion_percentage']:.2f}%)")
        return status

    def combine_chunks(self, output_filename: str = "final_results.csv", delete_chunks: bool = False) -> str:
        """
        Combine all chunk files into a single CSV with a header.

        Args:
            output_filename: Name of the merged output file.
            delete_chunks: Whether to delete individual chunk files after merging.

        Returns:
            Path to the combined file.
        """
        status = self.get_chunk_status()
        if status["missing_chunks"]:
            logger.warning(f"Missing {len(status['missing_chunks'])} chunks. Merging will be incomplete.")

        output_path = os.path.join(self.output_dir, output_filename)
        
        # Sort chunks to ensure correct order
        pattern = os.path.join(self.output_dir, f"fit_chunk_*_{self.chunk_size:05d}.csv")
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
        return output_path

    def fit_all_chunks(self, skip_finished: bool = True, max_chunks: Optional[int] = None, combine_at_end: bool = False) -> None:
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

    def launch_all_chunks_slurm(self, skip_finished: bool = True, max_chunks: Optional[int] = None) -> None:
        """
        Launch all missing chunks as a SLURM array job.

        Args:
            skip_finished: If True, only launches chunks that don't have an output file.
            max_chunks: Optional limit on the number of chunks to consider.
        """
        total_chunks = self.get_number_of_chunks()
        if max_chunks is not None:
            total_chunks = min(total_chunks, max_chunks)

        status = self.get_chunk_status()
        finished_chunks = set(status["finished_chunks"])
        
        chunks_to_launch = [i for i in range(total_chunks) if not (skip_finished and i in finished_chunks)]

        if not chunks_to_launch:
            logger.info("No chunks to launch.")
            return

        array_str = self._get_slurm_array_string(chunks_to_launch)
        
        if not hasattr(self, "slurm_launcher"):
            raise ValueError("slurm_launcher parameter is required in YAML for SLURM submission")
        
        launcher_path = self.slurm_launcher
        if not os.path.exists(launcher_path):
            raise FileNotFoundError(f"SLURM launcher script not found: {launcher_path}")

        cmd = [
            "sbatch",
            f"--array={array_str}",
            f"--ntasks={self.max_workers}",
            "--nodes=1",
            launcher_path,
            str(self.yaml_path)
        ]

        logger.info(f"Launching SLURM array job: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"SLURM output: {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to submit SLURM job: {e.stderr}")
            raise

    def _get_slurm_array_string(self, indices: list[int]) -> str:
        """
        Convert a list of indices into a SLURM array string (e.g., 0-5,7,10-12).
        """
        if not indices:
            return ""
        
        indices = sorted(indices)
        ranges = []
        for _, g in itertools.groupby(enumerate(indices), lambda x: x[0] - x[1]):
            group = list(g)
            start = group[0][1]
            end = group[-1][1]
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
        
        return ",".join(ranges)

if __name__ == "__main__":
    config = Trasgu("yaml_examples/geoocean.yaml")
    config.launch_all_chunks_slurm(skip_finished=True)
    
    #config.fit_vinecop_chunk_to_file(chunk_index=1)
    


    # print(config.get_matrix(10))
    # print(config._load_matrices_from_zarr(10, 100))
    # # print(config)
    
    # config.get_id_chunk_from_matrix_id(15000)º

    # Examples for doing the unittests    

    # Test 1: test has to take less than 1 minute.
#    config.measure_fitting_time()


    # # Test 2: n has to be equal to 660602880
    # n = config.get_number_of_trasgu_matrices()
    # print(n)

    # # Test 3:  n_chunks has to be equal to 6606029
    # n_chunks = config.get_number_of_chunks()
    # print(n_chunks)

    # # Test 4: chunk_id has to be equal to 60000
    # chunk_id = config.get_id_chunk_from_matrix_id(matrix_id=6000000)
    # print(chunk_id)

    # Test 5: Test that the second line of file fit_tests/fit_chunk_0001_00100.csv has this exact string "100,28,-10687.981736". 
    # Also: Obtain a variable with the time taken to run the command
#    config.fit_vinecop_chunk_to_file(chunk_index=1)



    # Test 6: tuple_range has to be (100,199)
    tuple_range= config.print_chunk_matrices_range(1)
    


    # start_time = time.perf_counter()
    # config.fit_vinecop_chunk_parallel()
    # elapsed_time = time.perf_counter() - start_time

    # print(f"Fitting completed in {elapsed_time:.2f} seconds")

    # print(config.get_number_of_chunks(27000))

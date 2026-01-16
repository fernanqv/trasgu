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
from concurrent.futures import ProcessPoolExecutor
import pickle
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("vine_config")


class VineConfig:
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
        self.yaml_path = Path(yaml_path)

        # Load YAML
        with open(self.yaml_path, "r") as f:
            config = yaml.safe_load(f)

        # Assign all YAML parameters as attributes
        for key, value in config.items():
            if not key.startswith("#"):  # Ignore comments
                setattr(self, key, value)

        if not hasattr(self, "chimera_url"):
            fs = fsspec.filesystem("http")
            self.chimera_store = fs.get_mapper(
                "https://geoocean.sci.unican.es/chimera/chimera.zarr"
            )
        else:
            # If .chimera_url is a local path, use local filesystem, else use HTTP
            if os.path.exists(self.chimera_url):
                self.chimera_store = self.chimera_url
            else:
                fs = fsspec.filesystem("http")
                self.chimera_store = fs.get_mapper(self.chimera_url)

        if not hasattr(self, "output_dir"):
            self.output_dir = "fit_results"

        if not hasattr(self, "chunk_size"):
            self.chunk_size = 30000

        if not hasattr(self, "parallel_tasks"):
            self.parallel_tasks = 1
        else:
            self.parallel_tasks = int(self.parallel_tasks)   

        if not hasattr(self, "controls_file"):
            self.controls = pv.FitControlsVinecop(
                family_set=pv.one_par,
                selection_criterion="aic",
                show_trace=False,
                parametric_method="mle",
            )
        else:
            with open(self.controls_file, "rb") as f:
                self.controls = pickle.load(f)

        self.data = self._get_data_from_file()
        self.n_vars = self.data.shape[1]

    def __repr__(self) -> str:
        """Human-readable representation of the configuration."""
        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        return f"VineConfig({attrs})"

    def _fit_vinecop_chunk_internal(
        self,
        chunk_index: int,
        matrices: np.ndarray,
        data: np.ndarray,
        chunk_size: Optional[int] = None,
    ) -> np.ndarray:
        results = []

        first_vine = chunk_index * chunk_size

        for offset, matrix in enumerate(matrices):
            vine_id = first_vine + offset

            cop = pv.Vinecop.from_data(data, matrix=matrix, controls=self.controls)
            aic = cop.aic()
            results.append((int(vine_id), int(cop.npars), aic))

            # MARCEL'S WAY: We have verified both ways give the same AIC
            # matrixVC = pv.Vinecop.from_structure(matrix=chimera7[vine_id])
            # selection = matrixVC.select(data=u, controls=self.controls)
            # matrixVC.fit(u)
            # aic2 = matrixVC.aic()

        results_array = np.array(results)
        results_array[:, :2] = results_array[:, :2].astype(int)
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

        root = zarr.open_group(self.chimera_store, mode="r")
        matrices = root[f"matrices{self.n_vars}"]
        data = matrices[start:end, :, :]
        return np.array(data)

    def _get_matrix_from_id(self, matrix_id: int) -> np.ndarray:
        """
        Get a single matrix by ID.

        Args:
            matrix_id: Index of the matrix.

        Returns:
            Numpy array of shape (1, n_vars, n_vars).
        """
        matrix = self._load_matrices_from_zarr(matrix_id, matrix_id + 1)
        return matrix

    def _get_data_from_file(self) -> np.ndarray:
        """
        Load data from the input file specified in config.

        Returns:
            Numpy array with the data.
        """
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Data file not found: {self.data_file}")
        return np.loadtxt(self.data_file)

    def get_number_of_chimera_matrices(self) -> int:
        """
        Get the total number of matrices in the Chimera Zarr file.

        Returns:
            Total number of matrices.
        """
        root = zarr.open_group(self.chimera_store, mode="r")
        matrices = root[f"matrices{self.n_vars}"]
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

        total_matrices = self.get_number_of_chimera_matrices()
        n_chunks = (total_matrices + chunk_size - 1) // chunk_size
        return n_chunks

    def fit_vinecop_chunk(
        self,
        chunk_index: int,
    ) -> np.ndarray:
        """Fit vine copulas for a contiguous chunk of vine structures.

        This function loads a dataset from `data_file`, converts it to pseudo-
        observations, and fits a vine copula for each matrix loaded from the
        corresponding chimera zarr file. Results are written to a CSV in
        `output_dir` and a list of tuples is returned.

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
        chunk_size = self.chunk_size
        logger.info(f"Fitting chunk {chunk_index} with size {chunk_size}")

        os.makedirs(self.output_dir, exist_ok=True)

        # Transformar datos en pseudo-observaciones
        first_vine = chunk_index * chunk_size
        data = pv.to_pseudo_obs(self.data)
        logger.info(f"Loading vines {first_vine} to {first_vine + chunk_size - 1}")
        matrices = self._load_matrices_from_zarr(first_vine, first_vine + chunk_size)
        results = self._fit_vinecop_chunk_internal(
            chunk_index, matrices, data, chunk_size
        )
        return results

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
        results = self.fit_vinecop_chunk(chunk_index)

        # Guardar resultados en CSV
        output_path = os.path.join(
            self.output_dir, f"fit_chunk_{chunk_index:04d}_{self.chunk_size:05d}.csv"
        )
        np.savetxt(
            output_path,
            results,
            delimiter=",",
            header="vine_id,n_parameters,aic",
            fmt="%d,%d,%.6f",
            comments="",
        )
        logger.info(f"Results saved to {output_path}")

    def fit_vinecop_chunk_parallel(self) -> Dict[int, Optional[BaseException]]:
        """Run multiple chunk fits in parallel and report failures."""

        with ProcessPoolExecutor(max_workers=8) as ex:
            futures = {
                chunk_id: ex.submit(self.fit_vinecop_chunk_to_file, chunk_id)
                for chunk_id in np.arange(8)
            }

        results: Dict[int, Optional[BaseException]] = {}
        for chunk_id, future in futures.items():
            try:
                future.result()
                results[chunk_id] = None
                logger.info(f"Chunk {chunk_id} completed successfully")
            except Exception as exc:  # noqa: BLE001
                results[chunk_id] = exc
                logger.error(f"Chunk {chunk_id} failed: {exc}")

        return results

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
            chunk_size: Number of matrices to fit (default: 1000)

        Returns:
           Time in minutes to fit a full chunk as per config.
        """
        chunk_size_short = 100
        first_vine = 0
        data = pv.to_pseudo_obs(self.data)
        logger.info(f"Loading vines {first_vine} to {first_vine + chunk_size_short - 1}")
        matrices = self._load_matrices_from_zarr(
            first_vine, first_vine + chunk_size_short
        )
        logger.info(f"Starting fit for {chunk_size_short} vine copulas...")
        start_time = time.perf_counter()
        self._fit_vinecop_chunk_internal(0, matrices, data, chunk_size=chunk_size_short)
        elapsed_time = time.perf_counter() - start_time

        time_per_chunk = elapsed_time / chunk_size_short * self.chunk_size / 60
        logger.info(
            f"Estimated time for full chunk ({self.chunk_size}): {time_per_chunk:.2f} minutes"
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
        logger.info(f"Matrix ID {matrix_id} is in chunk {chunk_index}")
        return chunk_index

    # MONITORING METHODS
    def monitor_fitting_progress(self) -> Dict[int, int]:
        """
        Monitor fitting progress by checking output CSV files.

        Returns:
            Dictionary mapping chunk indices to number of fitted vines.
        """
        progress = {}
        for file in os.listdir(self.output_dir):
            if file.startswith("fit_chunk_") and file.endswith(".csv"):
                chunk_index = int(file[len("fit_chunk_") : -len(".csv")])
                output_path = os.path.join(self.output_dir, file)
                with open(output_path, "r") as f:
                    n_lines = sum(1 for line in f) - 1  # Exclude header
                progress[chunk_index] = n_lines
        return progress

    def get_chunk_status_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive summary of chunk fitting progress.

        Returns:
            Dictionary containing:
            - total_chunks: Total number of chunks to process
            - chunks_completed: Number of chunks with results
            - chunks_pending: Number of chunks not yet processed
            - total_vines_processed: Total number of fitted vines
            - total_vines: Total number of vines to fit
            - percent_complete: Percentage of fitting completed
            - chunks_in_progress: Chunks that are partially completed
        """
        progress = self.monitor_fitting_progress()
        total_chunks = self.get_number_of_chunks()
        total_vines = self.get_number_of_chimera_matrices()
        
        # Count completed and partial chunks
        chunks_completed = 0
        chunks_in_progress = []
        total_vines_processed = 0
        
        for chunk_idx in range(total_chunks):
            if chunk_idx in progress:
                vines_in_chunk = progress[chunk_idx]
                total_vines_processed += vines_in_chunk
                
                # Check if chunk is complete
                expected_vines = min(self.chunk_size, total_vines - chunk_idx * self.chunk_size)
                if vines_in_chunk >= expected_vines:
                    chunks_completed += 1
                else:
                    chunks_in_progress.append((chunk_idx, vines_in_chunk, expected_vines))
        
        chunks_pending = total_chunks - chunks_completed - len(chunks_in_progress)
        percent_complete = (total_vines_processed / total_vines * 100) if total_vines > 0 else 0
        
        return {
            "total_chunks": total_chunks,
            "chunks_completed": chunks_completed,
            "chunks_pending": chunks_pending,
            "chunks_in_progress": chunks_in_progress,
            "total_vines_processed": total_vines_processed,
            "total_vines": total_vines,
            "percent_complete": percent_complete,
        }

    def display_chunk_status(self, view: str = "compact") -> None:
        """
        Display chunk fitting status with different visualization options.

        Parameters:
        -----------
        view : str
            Type of display:
            - "compact": Single-line summary with progress bar
            - "detailed": Table showing individual chunk status
            - "stats": Detailed statistics and summary
            - "all": All three views
        """
        summary = self.get_chunk_status_summary()
        
        if view in ["compact", "all"]:
            self._display_compact_view(summary)
        
        if view in ["detailed", "all"]:
            logger.info("")  # Add spacing
            self._display_detailed_view(summary)
        
        if view in ["stats", "all"]:
            logger.info("")  # Add spacing
            self._display_stats_view(summary)

    def _display_compact_view(self, summary: Dict[str, Any]) -> None:
        """Display compact progress view with progress bar."""
        percent = summary["percent_complete"]
        completed = summary["chunks_completed"]
        in_progress = len(summary["chunks_in_progress"])
        pending = summary["chunks_pending"]
        
        # Create progress bar
        bar_length = 40
        filled = int(bar_length * percent / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        logger.info("=" * 70)
        logger.info("CHUNK FITTING PROGRESS (COMPACT VIEW)")
        logger.info("=" * 70)
        logger.info(f"[{bar}] {percent:.1f}%")
        logger.info(f"Chunks: {completed} completed, {in_progress} in progress, {pending} pending")
        logger.info(f"Vines: {summary['total_vines_processed']:,} / {summary['total_vines']:,}")

    def _display_detailed_view(self, summary: Dict[str, Any]) -> None:
        """Display detailed table view of chunk status."""
        progress = self.monitor_fitting_progress()
        total_chunks = summary["total_chunks"]
        total_vines = summary["total_vines"]
        
        logger.info("=" * 70)
        logger.info("CHUNK FITTING STATUS (DETAILED VIEW)")
        logger.info("=" * 70)
        logger.info(f"{'Chunk':>6} | {'Status':>12} | {'Vines Fitted':>12} | {'Progress':>10}")
        logger.info("-" * 70)
        
        for chunk_idx in range(total_chunks):
            if chunk_idx in progress:
                vines_fitted = progress[chunk_idx]
                expected_vines = min(self.chunk_size, total_vines - chunk_idx * self.chunk_size)
                
                if vines_fitted >= expected_vines:
                    status = "✓ Completed"
                else:
                    status = f"⏳ {vines_fitted}/{expected_vines}"
                
                progress_pct = (vines_fitted / expected_vines * 100) if expected_vines > 0 else 0
                logger.info(f"{chunk_idx:>6} | {status:>12} | {vines_fitted:>12} | {progress_pct:>9.1f}%")
            else:
                expected_vines = min(self.chunk_size, total_vines - chunk_idx * self.chunk_size)
                logger.info(f"{chunk_idx:>6} | {'⏹ Pending':>12} | {'0':>12} | {'0.0%':>10}")

    def _display_stats_view(self, summary: Dict[str, Any]) -> None:
        """Display detailed statistics view."""
        total_chunks = summary["total_chunks"]
        chunks_completed = summary["chunks_completed"]
        chunks_in_progress = summary["chunks_in_progress"]
        chunks_pending = summary["chunks_pending"]
        total_vines_processed = summary["total_vines_processed"]
        total_vines = summary["total_vines"]
        percent_complete = summary["percent_complete"]
        
        logger.info("=" * 70)
        logger.info("CHUNK FITTING STATISTICS")
        logger.info("=" * 70)
        logger.info(f"Total chunks:        {total_chunks:>10,}")
        logger.info(f"Completed chunks:    {chunks_completed:>10,} ({chunks_completed/total_chunks*100:>5.1f}%)")
        logger.info(f"In progress chunks:  {len(chunks_in_progress):>10} ({len(chunks_in_progress)/total_chunks*100:>5.1f}%)")
        logger.info(f"Pending chunks:      {chunks_pending:>10,} ({chunks_pending/total_chunks*100:>5.1f}%)")
        logger.info("-" * 70)
        logger.info(f"Total vines fitted:  {total_vines_processed:>10,}")
        logger.info(f"Total vines:         {total_vines:>10,}")
        logger.info(f"Overall progress:    {percent_complete:>10.2f}%")
        logger.info("-" * 70)
        
        # Show chunks in progress details
        if chunks_in_progress:
            logger.info("\nChunks in progress:")
            for chunk_idx, fitted, expected in chunks_in_progress[:10]:  # Show top 10
                progress_pct = (fitted / expected * 100) if expected > 0 else 0
                logger.info(f"  Chunk {chunk_idx:>6}: {fitted:>6}/{expected:<6} vines ({progress_pct:>5.1f}%)")
            
            if len(chunks_in_progress) > 10:
                logger.info(f"  ... and {len(chunks_in_progress) - 10} more chunks in progress")


if __name__ == "__main__":
    config = VineConfig("tests.yaml")


    # print(config._get_matrix_from_id(10))
    # print(config._load_matrices_from_zarr(10, 100))
    # # print(config)
    
    # config.get_id_chunk_from_matrix_id(15000)º

    # Examples for doing the unittests    

    # Test 1: test has to take less than 1 minute.
    #config.measure_fitting_time()

    # Test 2: n has to be equal to 660602880
    n = config.get_number_of_chimera_matrices()
    print(n)

    # Test 3:  n_chunks has to be equal to 6606029
    n_chunks = config.get_number_of_chunks()
    print(n_chunks)

    # Test 4: chunk_id has to be equal to 60000
    chunk_id = config.get_id_chunk_from_matrix_id(matrix_id=6000000)
    print(chunk_id)

    # Test 4: Test that the second line of file fit_tests/fit_chunk_0001_00100.csv has this exact string "100,28,-10687.981736". 
    # Also: Obtain a variable with the time taken to run the command
    #config.fit_vinecop_chunk_to_file(chunk_index=1)


    # Test 6: tuple_range has to be (100,199)
    tuple_range= config.print_chunk_matrices_range(1)
    


    # print(config.fit_vinecop_chunk(chunk_index=0))
    # config.fit_vinecop_chunk_to_file(chunk_index=0)

    # Monitor progress with different views
    config.display_chunk_status(view="compact")  # Single-line summary
    config.display_chunk_status(view="detailed")  # Table of chunks
    config.display_chunk_status(view="stats")     # Detailed statistics
    config.display_chunk_status(view="all")       # All views combined

    # start_time = time.perf_counter()
    # config.fit_vinecop_chunk_parallel()
    # elapsed_time = time.perf_counter() - start_time

    # print(f"Fitting completed in {elapsed_time:.2f} seconds")

    # print(config.get_number_of_chunks(27000))

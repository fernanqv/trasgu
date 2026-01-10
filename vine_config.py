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
from typing import Optional, Dict, Any
import pyvinecopulib as pv
import os.path
import time
from concurrent.futures import ProcessPoolExecutor


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
            self.chimera_url = "https://geoocean.sci.unican.es/chimera/chimera.zarr"

        if not hasattr(self, "output_dir"):
            self.output_dir = "fit_results"

        if not hasattr(self, "chunk_size"):
            self.chunk_size = 30000

        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Data file not found: {self.data_file}")
        self.data = np.loadtxt(self.data_file)

        self.n_vars = self.data.shape[1]

    def __repr__(self) -> str:
        """Human-readable representation of the configuration."""
        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        return f"VineConfig({attrs})"

    def get_number_of_chimera_matrices(self) -> int:
        """
        Get the total number of matrices in the Chimera Zarr file.

        Returns:
            Total number of matrices.
        """
        fs = fsspec.filesystem("http")
        root = zarr.open_group(fs.get_mapper(self.chimera_url), mode="r")
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

    def load_matrices_from_zarr(self, start: int, end: int) -> np.ndarray:
        """
        Load matrices from Chimera Zarr.

        Args:
            start: Starting index (inclusive).
            end: Ending index (exclusive).

        Returns:
            Numpy array of shape (end-start, n_vars, n_vars).
        """
        fs = fsspec.filesystem("http")
        root = zarr.open_group(fs.get_mapper(self.chimera_url), mode="r")
        matrices = root[f"matrices{self.n_vars}"]
        data = matrices[start:end, :, :]
        return np.array(data)

    def get_matrix_from_id(self, matrix_id: int) -> np.ndarray:
        """
        Get a single matrix by ID.

        Args:
            matrix_id: Index of the matrix.

        Returns:
            Numpy array of shape (1, n_vars, n_vars).
        """
        matrix = self.load_matrices_from_zarr(matrix_id, matrix_id + 1)
        return matrix

    def get_data_from_file(self) -> np.ndarray:
        """
        Load data from the input file specified in config.

        Returns:
            Numpy array with the data.
        """
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Data file not found: {self.data_file}")
        return np.loadtxt(self.data_file)

    def fit_vinecop_chunk(
        self,
        chunk_index: int,
    ) -> np.ndarray:
        """Fit vine copulas for a contiguous chunk of vine structures.

        This function loads a dataset from `data_file`, converts it to pseudo-
        observations, and fits a vine copula for each matrix loaded from the
        corresponding chimera HDF5 file. Results are written to a CSV in
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
        print(f"Fitting chunk {chunk_index} with size {chunk_size}")

        os.makedirs(self.output_dir, exist_ok=True)

        # Transformar datos en pseudo-observaciones
        first_vine = chunk_index * chunk_size
        data = pv.to_pseudo_obs(self.data)
        print(f"Loading vines {first_vine} to {first_vine + chunk_size - 1}")
        matrices = self.load_matrices_from_zarr(first_vine, first_vine + chunk_size)
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
        corresponding chimera HDF5 file. Results are written to a CSV in
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
        output_path = os.path.join(self.output_dir, f"fit_chunk_{chunk_index:04d}_{self.chunk_size:05d}.csv")
        np.savetxt(
            output_path,
            results,
            delimiter=",",
            header="vine_id,n_parameters,aic",
            fmt="%d,%d,%.6f",
            comments="",
        )
        print(f"Results saved to {output_path}")

    def fit_vinecop_chunk_parallel(self) -> None:
        """Placeholder for parallel fitting method."""
    
        with ProcessPoolExecutor(max_workers=8) as ex:
            futures = [ex.submit(self.fit_vinecop_chunk_to_file, chunk_id) for chunk_id in np.arange(8)]

        # for f in futures:
        #     print(f.result())
        


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

            controls = pv.FitControlsVinecop(
                family_set=pv.one_par,
                selection_criterion="aic",
                show_trace=False,
                parametric_method="mle",
            )
            cop = pv.Vinecop.from_data(data, matrix=matrix, controls=controls)
            aic = cop.aic()
            results.append((int(vine_id), int(cop.npars), aic))

            # MARCEL'S WAY: We have verified both ways give the same AIC
            # matrixVC = pv.Vinecop.from_structure(matrix=chimera7[vine_id])
            # selection = matrixVC.select(data=u, controls=controls)
            # matrixVC.fit(u)
            # aic2 = matrixVC.aic()

        results_array = np.array(results)
        results_array[:, :2] = results_array[:, :2].astype(int)
        return results_array
    
    def print_chunk_matrices_range(
        self, chunk_index: int, chunk_size: Optional[int] = None
    ) -> None:
        """
        List matrices in a given chunk.

        Args:
            chunk_index: Zero-based index of the chunk.
            chunk_size: Number of matrices per chunk (default from config).
        """
        if chunk_size is None:
            chunk_size = self.chunk_size

        first_vine = chunk_index * chunk_size
        last_vine = first_vine + chunk_size

        print(
            f"Matrices in chunk {chunk_index} (vines {first_vine} to {last_vine - 1}):"
        )

    def measure_fitting_time(self) -> float:
        """Measure execution time for fitting a chunk of vine copulas.

        Args:
            chunk_size: Number of matrices to fit (default: 1000)

        Returns:
           Time in minutes to fit a full chunk as per config.
        """
        chunk_size_short=100
        first_vine = 0
        data = pv.to_pseudo_obs(self.data)
        print(f"Loading vines {first_vine} to {first_vine + chunk_size_short - 1}")
        matrices = self.load_matrices_from_zarr(first_vine, first_vine + chunk_size_short)
        print(f"Starting fit for {chunk_size_short} vine copulas...")
        start_time = time.perf_counter()
        self._fit_vinecop_chunk_internal(0, matrices, data, chunk_size=chunk_size_short)
        elapsed_time = time.perf_counter() - start_time

        time_per_chunk= elapsed_time / chunk_size_short * self.chunk_size /60
        print(f"Estimated time for full chunk ({self.chunk_size}): {time_per_chunk:.2f} minutes")

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
        print(f"Matrix ID {matrix_id} is in chunk {chunk_index}")
        return chunk_index

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



if __name__ == '__main__':
    config = VineConfig("minimal.yaml")

    # print(config.get_matrix_from_id(10))
    # print(config.load_matrices_from_zarr(10, 100))
    # # print(config)
    # config.print_chunk_matrices_range(0)
    # config.get_id_chunk_from_matrix_id(15000)

    print(config.measure_fitting_time())

    #print(config.fit_vinecop_chunk(chunk_index=0))
    #print(config.get_number_of_chimera_matrices())
    #config.fit_vinecop_chunk_to_file(chunk_index=0)

    # print(config.monitor_fitting_progress())
    # start_time = time.perf_counter()
    # config.fit_vinecop_chunk_parallel()
    # elapsed_time = time.perf_counter() - start_time

    # print(f"Fitting completed in {elapsed_time:.2f} seconds")

    #print(config.get_number_of_chunks(27000))



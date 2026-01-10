
import zarr
import fsspec
import numpy as np

def load_matrices_from_zarr(url, n_vars, start, end):

    fs = fsspec.filesystem("http")
    
    # 1) Abrir el grupo
    root = zarr.open_group(fs.get_mapper(url), mode="r")
    
    # 2) Acceder al array 'matrices7'
    matrices = root[f'matrices{n_vars}']
    
    # 3) Cargar las matrices desde start hasta end
    data = matrices[start:end, :, :]
    
    return np.array(data)


def get_matrix_from_id(url, n_vars, matrix_id):
    matrix=load_matrices_from_zarr(url, n_vars, matrix_id, matrix_id + 1)    
    return matrix


matrix=get_matrix_from_id("https://geoocean.sci.unican.es/chimera/chimera.zarr",7,10)
matrix_array=load_matrices_from_zarr("https://geoocean.sci.unican.es/chimera/chimera.zarr",7,10,100)
print(matrix)
print(matrix_array)



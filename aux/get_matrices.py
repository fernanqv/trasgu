import bz2
import _pickle as cPickle
import os
import numpy as np
import h5py


class matrix():
    def __init__(self, index, mat_type, matrix):
        self.index = index
        self.mat_type = mat_type
        self.matrix = np.flip(np.array(matrix),axis=0)

def decompress_pickle(file):
    # Load any compressed pickle file and return data
    data = bz2.BZ2File(file, 'rb')
    data = cPickle.load(data)
    return data

def get_matrices(matrix_dir,nodes=4,subtrees=[]):
    # EXTRACT INFO FROM CHIMERA FILES DOWNLOADED FROM CHIMERA DELFT REPO
    # MARCELL CHIMERA VINES
    # Get all files in the directory
    files =os.listdir(matrix_dir)
    files.sort()
    to_get = []
    if len(subtrees) == 0:
        for x in files:
            if "_" + str(nodes) + "_" in x:
                to_get.append(x)
    else:
        for x in files:
            for st in subtrees:
                if st in x:
                    to_get.append(x)
    matrices = []
    for dat_file in to_get:
        data = decompress_pickle(matrix_dir+dat_file)
        mat =[]
        index = 0
        mat_type= ""
        for line in data:
            if "Matrix" in line:
                if len(mat) != 0:
                    matrices.append(matrix(index,mat_type,mat))
                mat = []
                index = int(line.split()[-1])
            elif "Type" in line:
                mat_type = line.split()[-1]
            else:
                if len(line.split()) > 0:
                    row = [int(x) for x in line.split()]
                    mat.append(row)
        matrices.append(matrix(index, mat_type, mat))
    return matrices
def get_files(matrix_dir):
    # returns filnames in the specified directory
    return os.listdir(matrix_dir)

def save_matrices_to_h5(matrices_list, filename):
    """
    Saves the numpy matrices from a list of matrix objects to an HDF5 file.
    Access them later using:
    with h5py.File(filename, 'r') as f:
        mat = f['matrices'][index]
    """
    # Extract numpy arrays
 
    arrays = [np.asarray(m.matrix, dtype=np.uint8) for m in matrices_list]
    with h5py.File(filename, 'w') as f:
        data = np.stack(arrays)
        f.create_dataset('matrices', data=data, compression="gzip", chunks=True)


def load_matrices_from_h5(filename):
    """
    Loads matrices from an HDF5 file created by save_matrices_to_h5.
    Returns:
        - A single numpy array of shape (N, rows, cols) if they were saved stacked.
        - A list of numpy arrays if they were saved individually (variable sizes).
    """
    with h5py.File(filename, 'r') as f:
        # Check if 'matrices' is a single Dataset (stacked) or a Group (individual)
        if isinstance(f['matrices'], h5py.Dataset):
            print(f"Loading stacked matrices from {filename}...")
            return f['matrices'][:] # Load entire dataset into memory
            #return f['matrices'][0] # Load entire dataset into memory
        

if __name__ == "__main__":
    # define matrix dir
    #matrix_dir = "E:/databases_vines/"
    # get matrix files
    #files = get_files(matrix_dir)
    # get all matrices of a particular number of nodes
    matrices = get_matrices("./chimera/7/", nodes=7)
    save_matrices_to_h5(matrices, "matrices_nodes7.h5")


    # Leer
    # start_time = time.time()
    # with h5py.File('matrices_nodes7.h5', 'r') as f:
    #     matriz_5 = f['matrices'][5] # Lee y descomprime SOLO la matriz 5
    # print(f"Loading took {time.time() - start_time} seconds.")


    # # Example loading
    # start_time = time.time()
    # loaded_mats = load_matrices_from_h5("matrices_nodes7.h5")

    # print(f"Loaded data shape/length: {len(loaded_mats)}")
    # print(f"Loading took {time.time() - start_time} seconds.")
    
    # get all matrices of specified files
    #matrices_subtrees = get_matrices(matrix_dir, subtrees=['submats_5_T6.pbz2','submats_5_T8.pbz2'])


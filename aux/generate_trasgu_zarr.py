import h5py
import zarr
import os
import numpy as np
from tqdm import tqdm

def convert_h5_to_zarr(n_vars, h5_dir="chimera", zarr_path="chimera.zarr"):
    """
    Converts HDF5 matrices to Zarr format.
    """
    h5_file = os.path.join(h5_dir, f"chimera{n_vars}.h5")
    
    if not os.path.exists(h5_file):
        print(f"Error: {h5_file} not found.")
        return

    print(f"Opening {h5_file}...")
    with h5py.File(h5_file, "r") as f_h5:
        data = f_h5["matrices"]
        shape = data.shape
        chunks = data.chunks
        dtype = data.dtype
        
        print(f"Dataset 'matrices' found: shape={shape}, chunks={chunks}, dtype={dtype}")
        
        if zarr.__version__.startswith('3'):
            # Zarr V3 logic
            root = zarr.open(zarr_path, mode='a')
            dataset_name = f"matrices{n_vars}"
            
            if dataset_name in root:
                print(f"Dataset {dataset_name} already exists in {zarr_path}. Overwriting...")
                del root[dataset_name]
            
            print(f"Creating Zarr dataset {dataset_name} in {zarr_path} (Zarr V3)...")
            z_out = root.create_dataset(
                dataset_name, 
                shape=shape, 
                chunks=chunks, 
                dtype=dtype,
                compressors=[zarr.codecs.GzipCodec()]
            )
        else:
            # Zarr V2 logic
            store = zarr.DirectoryStore(zarr_path)
            root = zarr.group(store=store)
            dataset_name = f"matrices{n_vars}"
            
            if dataset_name in root:
                print(f"Dataset {dataset_name} already exists in {zarr_path}. Overwriting...")
                del root[dataset_name]
                
            print(f"Creating Zarr dataset {dataset_name} in {zarr_path} (Zarr V2)...")
            z_out = root.create_dataset(
                dataset_name, 
                shape=shape, 
                chunks=chunks, 
                dtype=dtype, 
                compressor=zarr.Blosc(cname='lz4', clevel=5, shuffle=zarr.Blosc.BITSHUFFLE)
            )
        
        # Copy data in chunks to be memory efficient for large files (like chimera8.h5)
        # Using the HDF5 chunks as a guide for step size
        chunk_size = chunks[0] if chunks else 1000
        
        print(f"Copying data to Zarr...")
        for i in tqdm(range(0, shape[0], chunk_size)):
            end = min(i + chunk_size, shape[0])
            z_out[i:end] = data[i:end]
            
    print(f"Finished converting {h5_file} to {zarr_path}/{dataset_name}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert Chimera HDF5 matrices to Zarr.")
    parser.add_argument("--vars", type=int, default=5, help="Number of variables (e.g., 5).")
    parser.add_argument("--all", action="store_true", help="Convert all available (4, 5, 6, 7, 8).")
    parser.add_argument("--h5_dir", type=str, default="chimera", help="Directory containing HDF5 files.")
    parser.add_argument("--zarr_path", type=str, default="chimera.zarr", help="Output Zarr store path.")
    
    args = parser.parse_args()
    
    if args.all:
        for v in [4, 5, 6, 7, 8]:
            convert_h5_to_zarr(v, args.h5_dir, args.zarr_path)
    else:
        convert_h5_to_zarr(args.vars, args.h5_dir, args.zarr_path)

#!/usr/bin/env python3
import sys
from pathlib import Path
import fsspec
import zarr
from trasgu.cli._shared import parser as make_parser

def main():
    parser = make_parser(
        "Download Chimera Zarr structure arrays to a local directory.",
        """
        Examples:
          trasgu_download_zarr /scratch/user
          trasgu_download_zarr /scratch/user --vars 4,5,6,7
          trasgu_download_zarr /scratch/user --vars 6 --url http://example.org/chimera.zarr

        Notes:
          Use this on a node with internet access before running trasgu on
          compute nodes without external network access.
          Point trasgu.yaml to the downloaded chimera.zarr store with trasgu_url.
          Variable size 8 is very large and requires interactive confirmation.
        """,
    )
    parser.add_argument(
        "destination",
        type=str,
        help="Directory where chimera.zarr should be created/updated.",
    )
    parser.add_argument(
        "--vars",
        type=str,
        default="4,5,6,7",
        help="Comma-separated list of variable sizes to download (e.g. 4,5,6,7,8). Default: 4,5,6,7. WARNING: size 8 is ~338GB.",
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://meteo.unican.es/work/chimera.zarr",
        help="Remote URL of the Chimera Zarr store.",
    )

    args = parser.parse_args()

    dest_path = Path(args.destination).resolve() / "chimera.zarr"
    print(f"Target directory: {dest_path}")

    # Parse variables to download
    try:
        var_sizes = [int(x.strip()) for x in args.vars.split(",") if x.strip()]
    except ValueError:
        print("Error: --vars must be a comma-separated list of integers.", file=sys.stderr)
        sys.exit(1)

    # Warn if size 8 is requested
    if 8 in var_sizes:
        print("WARNING: You have selected variable size 8. This array is ~3 GB and will take a long time to download.")
        response = input("Do you want to continue? [y/N]: ")
        if response.lower() not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

    print("Connecting to remote store...")
    try:
        fs = fsspec.filesystem("http")
        src_mapper = fs.get_mapper(args.url)
        src_grp = zarr.open_group(src_mapper, mode="r")
    except Exception as e:
        print(f"Error connecting to remote store: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Opening local store at {dest_path}...")
    try:
        dst_grp = zarr.open_group(str(dest_path), mode="a")
    except Exception as e:
        print(f"Error opening local store: {e}", file=sys.stderr)
        sys.exit(1)

    for n in var_sizes:
        name = f"matrices{n}"
        if name not in src_grp:
            print(f"Warning: Array '{name}' not found in remote store. Skipping.", file=sys.stderr)
            continue

        try:
            arr_src = src_grp[name]
            
            # Check if destination array already exists and matches shape/chunks
            if name in dst_grp:
                arr_dst = dst_grp[name]
                if arr_dst.shape == arr_src.shape and arr_dst.dtype == arr_src.dtype:
                    print(f"Array '{name}' already fully downloaded. Skipping.")
                    continue

            print(f"\nDownloading '{name}' (shape: {arr_src.shape}, chunks: {arr_src.chunks})...")
            arr_dst = dst_grp.create_array(
                name,
                shape=arr_src.shape,
                chunks=arr_src.chunks,
                dtype=arr_src.dtype,
                overwrite=True,
            )

            chunk_size = arr_src.chunks[0]
            total_elements = arr_src.shape[0]

            for start in range(0, total_elements, chunk_size):
                end = min(start + chunk_size, total_elements)
                print(f"  -> Downloading slice {start} to {end} ({end / total_elements * 100:.1f}%)...")
                arr_dst[start:end] = arr_src[start:end]

            print(f"Successfully downloaded '{name}'.")
        except Exception as e:
            print(f"Error downloading '{name}': {e}", file=sys.stderr)

    print("\nDownload complete.")

if __name__ == "__main__":
    main()

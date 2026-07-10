#!/usr/bin/env python3
import sys
from trasgu import Trasgu
from trasgu.cli._shared import parser as make_parser
from trasgu.cli._shared import run_directory_error

def main():
    parser = make_parser(
        "Fit one zero-based Chimera matrix chunk and write its CSV output.",
        """
        Examples:
          trasgu_examples minimal ./minimal
          cd minimal
          trasgu_fit_chunk 0
          trasgu_fit_chunk 23

        Notes:
          Run from a directory containing trasgu.yaml.
          This command is used by the Snakemake workflow and is also useful
          for debugging or rerunning one missing chunk.
          Output files are written as fit_chunk_NNNN_MMMMM.csv under output_dir.
        """,
    )
    parser.add_argument("chunk_id", type=int, help="Zero-based index of the chunk to process.")

    args = parser.parse_args()

    try:
        config = Trasgu()
        config.fit_vinecop_chunk_to_file(args.chunk_id)
    except Exception as e:
        print(f"Error processing chunk {args.chunk_id}: {run_directory_error(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

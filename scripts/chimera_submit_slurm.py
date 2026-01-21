#!/usr/bin/env python3
import argparse
import logging
from chimera_vines import ChimeraVines

def main():
    parser = argparse.ArgumentParser(description="Submit missing vine copula chunks to a SLURM cluster.")
    parser.add_argument("config", help="Path to the YAML configuration file.")
    parser.add_argument("--max-chunks", "-m", type=int, help="Limit the number of chunks to consider.")
    parser.add_argument("--no-skip", action="store_false", dest="skip_finished", help="Launch all chunks even if they are already finished.")
    parser.set_defaults(skip_finished=True)

    args = parser.parse_args()

    try:
        config = ChimeraVines(args.config)
        config.launch_all_chunks_slurm(
            skip_finished=args.skip_finished,
            max_chunks=args.max_chunks
        )
    except Exception as e:
        # ChimeraVines sets up its own logger named 'vine_config'
        logging.getLogger("vine_config").error(f"SLURM submission failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()

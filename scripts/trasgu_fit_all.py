#!/usr/bin/env python3
import argparse
import logging
from trasgu import Trasgu

def main():
    parser = argparse.ArgumentParser(description="Run vine copula fitting for all chunks.")
    parser.add_argument("config", help="Path to the YAML configuration file.")
    parser.add_argument("--max-chunks", "-m", type=int, help="Limit the number of chunks to process.")
    parser.add_argument("--no-combine", action="store_false", dest="combine", help="Do not combine results after fitting.")
    parser.set_defaults(combine=True)
    parser.add_argument("--no-skip", action="store_false", dest="skip_finished", help="Do not skip finished chunks.")

    args = parser.parse_args()

    # Instantiate the class with the provided config file
    try:
        config = Trasgu(args.config)
        
        # Run the fitting process
        config.fit_all_chunks(
            skip_finished=args.skip_finished,
            max_chunks=args.max_chunks,
            combine_at_end=args.combine
        )
    except Exception as e:
        # We don't need to re-log level here as Trasgu already set up logging
        logging.getLogger("vine_config").error(f"Execution failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()

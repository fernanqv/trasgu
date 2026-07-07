#!/usr/bin/env python3
import logging
import sys
import time
from trasgu import Trasgu
from scripts._cli import parser as make_parser
from scripts._cli import run_directory_error

def print_status(status):
    print("\n--- Processing Status ---")
    print(f"Total Chunks:   {status['total_chunks']}")
    print(f"Finished:       {status['finished_chunks_count']}")
    print(f"Completion:     {status['completion_percentage']:.2f}%")
    
    if status['missing_chunks']:
        print(f"Missing chunks count: {len(status['missing_chunks'])}")
        if len(status['missing_chunks']) <= 20:
            print(f"Missing IDs: {status['missing_chunks']}")
        else:
            print(f"First 10 missing IDs: {status['missing_chunks'][:10]}")
    else:
        print("All chunks finished!")
    print("-" * 25)

def main():
    parser = make_parser(
        "Show progress for chunk CSV files in the current trasgu run directory.",
        """
        Examples:
          cd examples/run_config/minimal
          trasgu_monitor
          trasgu_monitor --watch 30

        Notes:
          Run from a directory containing trasgu.yaml.
          Progress is based on fit_chunk_*.csv files found under output_dir.
          Press Ctrl+C to stop watch mode.
        """,
    )
    parser.add_argument("--watch", "-w", type=int, help="Refresh interval in seconds.")

    args = parser.parse_args()

    try:
        config = Trasgu()
        
        while True:
            status = config.get_chunk_status()
            print_status(status)
            
            if args.watch:
                time.sleep(args.watch)
            else:
                break
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
    except Exception as e:
        logging.getLogger("vine_config").error(f"Monitoring failed: {run_directory_error(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

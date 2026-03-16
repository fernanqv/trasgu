#!/usr/bin/env python3
import argparse
import logging
import sys
import time
from trasgu import Trasgu

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
    parser = argparse.ArgumentParser(description="Monitor the status of chunk processing.")
    parser.add_argument("config", help="Path to the YAML configuration file.")
    parser.add_argument("--watch", "-w", type=int, help="Refresh interval in seconds (simulates watch mode).")

    args = parser.parse_args()

    try:
        config = Trasgu(args.config)
        
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
        logging.getLogger("vine_config").error(f"Monitoring failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

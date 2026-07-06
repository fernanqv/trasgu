#!/usr/bin/env python3
import sys


def main():
    print(
        "trasgu_submit_slurm is deprecated. Use 'trasgu_run --profile slurm' "
        "from a run directory containing trasgu.yaml.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import sys


def main():
    print(
        "trasgu_fit_all is deprecated. Use 'trasgu_run' from a run directory "
        "containing trasgu.yaml.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()

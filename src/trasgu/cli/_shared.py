import argparse
import textwrap


RUN_DIRECTORY_NOTE = (
    "Run this command from a run directory containing trasgu.yaml. "
    "Relative paths in trasgu.yaml are resolved from that directory."
)


def parser(description: str, epilog: str) -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description=description,
        epilog=textwrap.dedent(epilog).strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def run_directory_error(error: Exception) -> str:
    return f"{error}\n\n{RUN_DIRECTORY_NOTE}"

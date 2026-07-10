#!/usr/bin/env python3
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path
import sys

from trasgu.cli._shared import parser as make_parser


EXAMPLES = (
    "minimal",
    "csv_columns",
    "local_chimera",
    "custom_controls",
    "parallel_debug",
    "profiles",
)


def _examples_root() -> Traversable:
    return resources.files("trasgu.examples")


def _copy_resource_tree(source: Traversable, destination: Path, *, force: bool) -> None:
    if source.name in {"__pycache__", "__init__.py"} or source.name.endswith(".pyc"):
        return

    if source.is_dir():
        destination.mkdir(parents=True, exist_ok=True)
        for child in source.iterdir():
            _copy_resource_tree(child, destination / child.name, force=force)
        return

    if destination.exists() and not force:
        raise FileExistsError(destination)

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())


def _print_examples() -> None:
    print("Available examples:")
    for name in EXAMPLES:
        print(f"  {name}")
    print("  all")


def main() -> None:
    parser = make_parser(
        "Copy packaged trasgu examples to a local working directory.",
        """
        Examples:
          trasgu_examples --list
          trasgu_examples minimal ./my-run
          cd ./my-run
          trasgu_run --dry-run
          trasgu_examples profiles ./profiles
          trasgu_examples all ./trasgu_examples

        Notes:
          Run examples are copied as self-contained directories.
          Existing files are left untouched unless --force is used.
        """,
    )
    parser.add_argument(
        "example",
        nargs="?",
        choices=EXAMPLES + ("all",),
        help="Example to copy. Use 'all' to copy every packaged example.",
    )
    parser.add_argument(
        "destination",
        nargs="?",
        default=None,
        help="Destination directory. Defaults to ./<example> or ./trasgu_examples for all.",
    )
    parser.add_argument("--list", action="store_true", help="List examples and exit.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files in the destination.",
    )

    args = parser.parse_args()

    if args.list or args.example is None:
        _print_examples()
        return

    destination_name = args.destination
    if destination_name is None:
        destination_name = "trasgu_examples" if args.example == "all" else args.example
    destination = Path(destination_name).expanduser().resolve()

    try:
        if args.example == "all":
            _copy_resource_tree(_examples_root(), destination, force=args.force)
        else:
            _copy_resource_tree(
                _examples_root() / args.example,
                destination,
                force=args.force,
            )
    except FileExistsError as e:
        print(
            f"Error: {e} already exists. Use --force to overwrite existing files.",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Copied '{args.example}' example files to {destination}")


if __name__ == "__main__":
    main()

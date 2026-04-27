"""Command-line interface for streamdiff."""

import argparse
import sys

from streamdiff.differ import ChangeType, diff_streams


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="streamdiff",
        description="Diff two sorted line-based datasets without loading them fully into memory.",
    )
    parser.add_argument("file_a", help="Old file (use '-' for stdin)")
    parser.add_argument("file_b", help="New file")
    parser.add_argument(
        "--show-unchanged",
        action="store_true",
        default=False,
        help="Also print lines that are identical in both files.",
    )
    parser.add_argument(
        "--only",
        choices=["added", "removed"],
        default=None,
        help="Restrict output to only added or only removed lines.",
    )
    parser.add_argument(
        "--count",
        action="store_true",
        default=False,
        help="Print summary counts instead of individual lines.",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    counts = {ChangeType.ADDED: 0, ChangeType.REMOVED: 0, ChangeType.UNCHANGED: 0}

    try:
        for record in diff_streams(args.file_a, args.file_b, show_unchanged=args.show_unchanged):
            counts[record.change] += 1
            if not args.count:
                if args.only is None or record.change.value == args.only:
                    print(record)
    except FileNotFoundError as exc:
        print(f"streamdiff: error: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        return 0

    if args.count:
        print(f"added:     {counts[ChangeType.ADDED]}")
        print(f"removed:   {counts[ChangeType.REMOVED]}")
        if args.show_unchanged:
            print(f"unchanged: {counts[ChangeType.UNCHANGED]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

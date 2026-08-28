#!/usr/bin/env python3
"""Build the whole Sahityika reading archive from the raw chat export.

    python3 scripts/build.py                      # uses config/settings.json
    python3 scripts/build.py --source data/raw/oldmessages.json
    python3 scripts/build.py --duration 90        # override normalised length

Everything it writes lands in data/processed/ and data/reports/.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sahityika import outputs
from sahityika.aggregate import build_authors, build_readers, build_works
from sahityika.config import load_config
from sahityika.parsing import parse_messages
from sahityika.report import write_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        help="Raw export to read (default: source_file in config/settings.json)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        help="Normalised session length in minutes (default: from settings)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Directory for processed files (default: from settings)",
    )
    return parser.parse_args()


def load_messages(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        return data.get("messages", [])
    if isinstance(data, list):
        return data
    raise ValueError(f"Unexpected JSON shape in {path}")


def main() -> int:
    args = parse_args()
    config = load_config()

    if args.duration:
        config.settings["default_duration_minutes"] = args.duration

    source = args.source or config.source_file
    if not source.is_absolute():
        source = Path.cwd() / source
    if not source.exists():
        print(f"error: source file not found: {source}", file=sys.stderr)
        return 1

    out_dir = args.out or config.output_dir
    report_dir = config.report_dir

    messages = load_messages(source)
    sessions, skipped = parse_messages(messages, config)

    if not sessions:
        print("error: no reading sessions found - has the export format changed?", file=sys.stderr)
        return 1

    works = build_works(sessions, config)
    readers = build_readers(sessions, works)
    authors = build_authors(works)

    written: list[tuple[str, int]] = [
        ("sessions.csv", outputs.write_sessions(out_dir / "sessions.csv", sessions, config)),
        ("sessions_detailed.csv", outputs.write_sessions_detailed(out_dir / "sessions_detailed.csv", sessions, config)),
        ("works.csv", outputs.write_works(out_dir / "works.csv", works, config)),
        ("work_readers.csv", outputs.write_work_readers(out_dir / "work_readers.csv", works, config)),
        ("readers.csv", outputs.write_readers(out_dir / "readers.csv", readers)),
        ("authors.csv", outputs.write_authors(out_dir / "authors.csv", authors)),
        ("timeline.csv", outputs.write_timeline(out_dir / "timeline.csv", works)),
        ("archive.json", outputs.write_archive(out_dir / "archive.json", sessions, works)),
    ]

    report_path = write_report(
        report_dir / "audit.md", sessions, works, skipped, config
    )

    total_hours = round(sum(s.duration_minutes for s in sessions) / 60, 1)
    unassigned = sum(1 for s in sessions if not s.readers)
    missing_author = sum(
        1 for w in works if not w.author and w.work_type != "Club Activity"
    )

    print("=" * 62)
    print("SAHITYIKA READING ARCHIVE")
    print("=" * 62)
    print(f"source            : {source.relative_to(Path.cwd()) if source.is_relative_to(Path.cwd()) else source}")
    print(f"messages scanned  : {len(messages)}")
    print(f"sessions parsed   : {len(sessions)}")
    print(f"distinct works    : {len(works)}")
    print(f"distinct readers  : {len(readers)}")
    print(f"credited authors  : {len(authors)}")
    print(f"reading time      : {total_hours} h (normalised @ {config.default_duration} min)")
    print(f"date range        : {outputs.iso_date(sessions[0].start)} -> {outputs.iso_date(sessions[-1].start)}")
    print()
    print(f"sessions w/o reader : {unassigned}")
    print(f"works w/o author    : {missing_author}")
    print(f"messages skipped    : {len(skipped)}")
    print()
    print("written:")
    for name, count in written:
        print(f"  {name:<24} {count:>4} rows")
    print(f"  {report_path.name:<24}      (audit notes)")

    print()
    print("Most-read works:")
    for work in works[:10]:
        author = f" - {work.author}" if work.author else ""
        print(f"  {work.sessions:>3} sessions | {work.title}{author}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

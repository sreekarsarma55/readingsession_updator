"""Writes the processed CSV and JSON files."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

from .aggregate import Person, Work
from .config import Config
from .parsing import Session


JOIN = "; "


def iso_datetime(value: datetime | None) -> str:
    """2022-12-12T23:05:00+05:30 - sorts correctly as plain text."""
    return value.isoformat(timespec="seconds") if value else ""


def iso_date(value: datetime | None) -> str:
    return value.date().isoformat() if value else ""


def readable(value: datetime | None) -> str:
    if not value:
        return ""
    return value.strftime("%d %b %Y, %I:%M %p").replace(" 0", " ")


def _write_csv(path: Path, header: Sequence[str], rows: Iterable[Sequence[Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)
            count += 1
    return count


# --------------------------------------------------------------------------
# sessions.csv - the requested schema
# --------------------------------------------------------------------------


def write_sessions(path: Path, sessions: list[Session], config: Config) -> int:
    """One row per session, in the exact requested column order.

    Deliberately one row per *session* rather than per reader: a co-read
    session is still a single two-hour meeting, so splitting it into two rows
    would double-count Duration_Minutes. Co-readers share the Reader cell.
    """
    rows = []
    for session in sessions:
        rows.append(
            [
                session.title,
                JOIN.join(session.readers) or config.unassigned_label,
                session.segment,
                iso_datetime(session.start),
                iso_datetime(session.end),
                session.duration_minutes,
            ]
        )

    return _write_csv(
        path,
        ["Title", "Reader", "Segment", "Created_Date", "Stopped_At", "Duration_Minutes"],
        rows,
    )


def write_sessions_detailed(path: Path, sessions: list[Session], config: Config) -> int:
    """Everything we know about each session, for auditing and traceability."""
    rows = []
    for session in sessions:
        rows.append(
            [
                iso_date(session.start),
                session.start.strftime("%A"),
                iso_datetime(session.start),
                iso_datetime(session.end),
                session.duration_minutes,
                session.title,
                session.primary.author if session.primary else "",
                session.segment,
                session.category,
                JOIN.join(w.title for w in session.additional_works),
                JOIN.join(session.readers) or config.unassigned_label,
                len(session.readers),
                "yes" if session.readers_tentative else "",
                session.announced_by,
                session.announced_date_raw,
                session.announced_time_raw,
                iso_datetime(session.message_timestamp),
                JOIN.join(session.warnings),
                session.message_id,
            ]
        )

    return _write_csv(
        path,
        [
            "Date",
            "Weekday",
            "Created_Date",
            "Stopped_At",
            "Duration_Minutes",
            "Title",
            "Author",
            "Segment",
            "Announced_As",
            "Also_In_Session",
            "Readers",
            "Reader_Count",
            "Readers_Tentative",
            "Announced_By",
            "Announced_Date_Raw",
            "Announced_Time_Raw",
            "Message_Timestamp_UTC",
            "Warnings",
            "Message_Id",
        ],
        rows,
    )


# --------------------------------------------------------------------------
# works
# --------------------------------------------------------------------------


_WORKS_HEADER = [
    # --- consumed by the website's ReadingWork importer ---
    "Title",
    "Author",
    "Category",
    "Actual_Type",
    "Genre",
    "Language",
    "Country",
    "Status",
    "Sessions",
    "First_Date",
    "Last_Date",
    # --- extra context for humans, ignored by the importer ---
    "Hours",
    "Reader_Count",
    "Readers",
    "Segments_Covered",
    "Author_Confidence",
    "Notes",
]


def _work_row(work: Work, config: Config) -> list[Any]:
    return [
        work.title,
        work.author,
        config.site_category(work.announced_as),
        work.work_type,
        work.genre,
        work.language,
        work.country,
        work.status,
        work.sessions,
        iso_date(work.first_session),
        iso_date(work.last_session),
        round(work.total_minutes / 60, 1),
        work.reader_count,
        JOIN.join(work.readers),
        JOIN.join(work.segments),
        work.confidence,
        work.note,
    ]


def write_works(path: Path, works: list[Work], config: Config) -> int:
    """Published works, most-read first - the website's reading list.

    The leading columns use the exact names and order of the ReadingWork
    importer (title, author, category, actual_type, genre, language, country,
    status, sessions, first_date, last_date), so the file drops straight into
    the Django admin. `category` is lower-cased and folded onto the model's
    CATEGORY_CHOICES. Columns after `Last_Date` are extra context; the importer
    ignores what it does not recognise.

    The club's own segments are excluded and written to club_activities.csv
    instead, so the site's reading list stays a list of actual books.
    """
    rows = [_work_row(w, config) for w in works if not w.is_club_activity]
    return _write_csv(path, _WORKS_HEADER, rows)


def write_club_activities(path: Path, works: list[Work], config: Config) -> int:
    """The club's own recurring segments, kept out of the reading list.

    These ran alongside a reading ("Salem's Lot + Ink What You Think") and are
    part of the club's history, but they are not published works. Import them
    only if you want them on the site, using category "other".
    """
    rows = [_work_row(w, config) for w in works if w.is_club_activity]
    return _write_csv(path, _WORKS_HEADER, rows)


def write_work_readers(path: Path, works: list[Work], config: Config) -> int:
    """One row per work listing everyone who read it.

    A work appears exactly once no matter how many sessions or readers it had;
    multiple readers are collapsed into the Readers column and also counted.
    """
    rows = []
    for work in sorted(works, key=lambda w: (w.title.casefold(), w.author.casefold())):
        rows.append(
            [
                work.title,
                work.author,
                work.reader_count,
                JOIN.join(work.readers) or config.unassigned_label,
                work.sessions,
                iso_date(work.first_session),
                iso_date(work.last_session),
            ]
        )

    return _write_csv(
        path,
        [
            "Title",
            "Author",
            "Reader_Count",
            "Readers",
            "Sessions",
            "First_Session",
            "Last_Session",
        ],
        rows,
    )


# --------------------------------------------------------------------------
# people
# --------------------------------------------------------------------------


def write_readers(path: Path, readers: list[Person]) -> int:
    rows = []
    for person in readers:
        rows.append(
            [
                person.name,
                person.sessions,
                len(person.works),
                round(person.total_minutes / 60, 1),
                iso_date(person.first_session),
                iso_date(person.last_session),
                JOIN.join(person.works),
            ]
        )

    return _write_csv(
        path,
        [
            "Reader",
            "Sessions",
            "Works",
            "Hours",
            "First_Session",
            "Last_Session",
            "Works_Read",
        ],
        rows,
    )


def write_authors(path: Path, authors: list[dict[str, Any]]) -> int:
    rows = [
        [
            entry["Author"],
            entry["Works"],
            entry["Sessions"],
            JOIN.join(entry["Titles"]),
        ]
        for entry in authors
    ]
    return _write_csv(path, ["Author", "Works", "Sessions", "Titles"], rows)


# --------------------------------------------------------------------------
# timeline + archive
# --------------------------------------------------------------------------


def write_timeline(path: Path, works: list[Work]) -> int:
    """Works in the order the club started reading them."""
    ordered = sorted(
        works,
        key=lambda w: (w.first_session or datetime.max.replace(tzinfo=None), w.title.casefold()),
    )

    rows = []
    for index, work in enumerate(ordered, start=1):
        span = ""
        if work.first_session and work.last_session:
            span = (work.last_session.date() - work.first_session.date()).days
        rows.append(
            [
                index,
                iso_date(work.first_session),
                iso_date(work.last_session),
                span,
                work.title,
                work.author,
                work.work_type,
                work.sessions,
                JOIN.join(work.readers),
            ]
        )

    return _write_csv(
        path,
        [
            "Order",
            "First_Session",
            "Last_Session",
            "Span_Days",
            "Title",
            "Author",
            "Type",
            "Sessions",
            "Readers",
        ],
        rows,
    )


def write_archive(path: Path, sessions: list[Session], works: list[Work]) -> int:
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "session_count": len(sessions),
        "work_count": len(works),
        "sessions": [
            {
                "created_date": iso_datetime(session.start),
                "stopped_at": iso_datetime(session.end),
                "duration_minutes": session.duration_minutes,
                "title": session.title,
                "author": session.primary.author if session.primary else "",
                "segment": session.segment,
                "announced_as": session.category,
                "readers": session.readers,
                "readers_tentative": session.readers_tentative,
                "also_in_session": [w.title for w in session.additional_works],
                "announced_by": session.announced_by,
                "message_timestamp_utc": iso_datetime(session.message_timestamp),
                "message_id": session.message_id,
                "warnings": session.warnings,
            }
            for session in sessions
        ],
        "works": [
            {
                "title": work.title,
                "author": work.author,
                "type": work.work_type,
                "language": work.language,
                "country": work.country,
                "sessions": work.sessions,
                "hours": round(work.total_minutes / 60, 1),
                "readers": work.readers,
                "segments": work.segments,
                "first_session": iso_date(work.first_session),
                "last_session": iso_date(work.last_session),
                "author_confidence": work.confidence,
                "note": work.note,
            }
            for work in works
        ],
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    return len(sessions)

"""Rolls the flat list of sessions up into works, readers and authors."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .config import Config
from .parsing import Session, WorkRef


@dataclass
class Work:
    title: str
    author: str = ""
    work_type: str = ""
    language: str = ""
    country: str = ""
    confidence: str = ""
    note: str = ""

    sessions: int = 0
    primary_sessions: int = 0
    total_minutes: int = 0
    readers: list[str] = field(default_factory=list)
    segments: list[str] = field(default_factory=list)
    categories: Counter = field(default_factory=Counter)
    first_session: datetime | None = None
    last_session: datetime | None = None

    @property
    def announced_as(self) -> str:
        if not self.categories:
            return ""
        return self.categories.most_common(1)[0][0]

    @property
    def reader_count(self) -> int:
        return len(self.readers)


@dataclass
class Person:
    name: str
    sessions: int = 0
    total_minutes: int = 0
    works: list[str] = field(default_factory=list)
    first_session: datetime | None = None
    last_session: datetime | None = None


def _resolve_authors(
    sessions: list[Session], config: Config
) -> dict[str, dict[str, str]]:
    """Decide the author for every title.

    Titles are grouped case-insensitively. Within a title:
      * no author was ever announced -> take the curated author from config
      * exactly one author announced  -> use it for every session of that title
      * several authors announced     -> genuinely different works that happen
                                         to share a title (both "Submission"
                                         pieces), so keep them apart.

    Returns {title_key: {scraped_author_key: resolved_author}}.
    """
    announced: dict[str, set[str]] = defaultdict(set)
    display: dict[str, str] = {}

    for session in sessions:
        for ref in session.works:
            key = ref.title.casefold()
            display.setdefault(key, ref.title)
            if ref.author:
                announced[key].add(ref.author)

    resolved: dict[str, dict[str, str]] = {}
    for key, title in display.items():
        authors = sorted(announced.get(key, set()))
        meta = config.work_meta(title)
        curated = meta.get("author", "")

        if len(authors) <= 1:
            single = curated or (authors[0] if authors else "")
            resolved[key] = {"": single}
            if authors:
                resolved[key][authors[0].casefold()] = single
        else:
            # Distinct works sharing a title: keep each announced author.
            resolved[key] = {a.casefold(): a for a in authors}
            resolved[key][""] = ""

    return resolved


def build_works(sessions: list[Session], config: Config) -> list[Work]:
    author_map = _resolve_authors(sessions, config)
    works: dict[tuple[str, str], Work] = {}

    def resolve(ref: WorkRef) -> tuple[str, str]:
        key = ref.title.casefold()
        mapping = author_map.get(key, {})
        author = mapping.get(ref.author.casefold(), mapping.get("", ref.author))
        return key, author

    for session in sessions:
        for position, ref in enumerate(session.works):
            title_key, author = resolve(ref)
            work_key = (title_key, author.casefold())

            work = works.get(work_key)
            if work is None:
                meta = config.work_meta(ref.title, author)
                work = Work(
                    title=ref.title,
                    author=author,
                    work_type=meta.get("type", ""),
                    language=meta.get("language", ""),
                    country=meta.get("country", ""),
                    confidence=meta.get("confidence", "unverified"),
                    note=meta.get("note", ""),
                )
                works[work_key] = work

            work.sessions += 1
            work.categories[session.category] += 1

            if position == 0:
                # Duration is credited to the session's primary work only, so
                # that summing Total_Minutes across works gives the true total.
                work.primary_sessions += 1
                work.total_minutes += session.duration_minutes

            for reader in session.readers:
                if reader not in work.readers:
                    work.readers.append(reader)

            if session.segment and session.segment not in work.segments:
                work.segments.append(session.segment)

            if work.first_session is None or session.start < work.first_session:
                work.first_session = session.start
            if work.last_session is None or session.start > work.last_session:
                work.last_session = session.start

    for work in works.values():
        work.readers.sort(key=str.casefold)
        work.segments.sort(key=_segment_sort_key)

    return sorted(works.values(), key=work_sort_key)


def work_sort_key(work: Work) -> tuple[int, int, str]:
    """Most-read works first; the club's own segments drop to the bottom so the
    list reads as 'what we read' rather than 'what we did'."""
    return (
        1 if work.work_type == "Club Activity" else 0,
        -work.sessions,
        work.title.casefold(),
    )


def _segment_sort_key(segment: str) -> tuple[int, float, str]:
    """Sort "Chapter 2" before "Chapter 10", and named parts last."""
    digits = "".join(c if c.isdigit() else " " for c in segment).split()
    if digits:
        return (0, float(digits[0]), segment.casefold())
    return (1, 0.0, segment.casefold())


def build_readers(sessions: list[Session], works: list[Work]) -> list[Person]:
    people: dict[str, Person] = {}

    for session in sessions:
        for name in session.readers:
            person = people.setdefault(name, Person(name=name))
            person.sessions += 1
            person.total_minutes += session.duration_minutes
            if session.title and session.title not in person.works:
                person.works.append(session.title)
            if person.first_session is None or session.start < person.first_session:
                person.first_session = session.start
            if person.last_session is None or session.start > person.last_session:
                person.last_session = session.start

    for person in people.values():
        person.works.sort(key=str.casefold)

    return sorted(people.values(), key=lambda p: (-p.sessions, p.name.casefold()))


def build_authors(works: list[Work]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}

    for work in works:
        if not work.author:
            continue
        entry = grouped.setdefault(
            work.author,
            {"Author": work.author, "Works": 0, "Sessions": 0, "Titles": []},
        )
        entry["Works"] += 1
        entry["Sessions"] += work.sessions
        entry["Titles"].append(work.title)

    for entry in grouped.values():
        entry["Titles"].sort(key=str.casefold)

    return sorted(
        grouped.values(),
        key=lambda e: (-e["Sessions"], -e["Works"], e["Author"].casefold()),
    )

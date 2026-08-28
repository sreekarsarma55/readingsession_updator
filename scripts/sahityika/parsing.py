"""Turns raw exported chat messages into structured Session records.

A reading-session announcement looks like this (markdown varies wildly):

    Reading Sessions : A Chapter A Day
    Date : 12th, December, 2022
    Time : 11:05 PM
    Book : Lord of the Flies (Chapter 05)
    Reader : Angana Mondal
    Link : https://meet.google.com/...

Only the work label (Book/Novel/Story/...) is mandatory for a message to
count as a session.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .config import Config
from . import normalize as nz


# --------------------------------------------------------------------------
# Regexes
# --------------------------------------------------------------------------

def _label_pattern(labels: list[str]) -> re.Pattern[str]:
    """Match "Book : Title" and every markdown variant of it.

    The important detail: the bold markers may sit *before* the colon
    (`*Book* : *Title*`) as well as after it. The previous version of this
    pipeline used `Book\\s*:` and therefore silently dropped every message
    written in that style.
    """
    alternatives = "|".join(re.escape(label) for label in labels)
    return re.compile(
        rf"^[\s>]*[*_~`]*\s*(?P<label>{alternatives})\s*[*_~`]*\s*:\s*(?P<value>.+?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )


def _field_pattern(name: str) -> re.Pattern[str]:
    return re.compile(
        rf"^[\s>]*[*_~`]*\s*{re.escape(name)}\s*[*_~`]*\s*:\s*(?P<value>.*?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )


READER_RE = _field_pattern("Reader")
READERS_RE = _field_pattern("Readers")
DATE_RE = _field_pattern("Date")
TIME_RE = _field_pattern("Time")

# "Monday, December 12, 2022 at 5:30:58PM UTC" (the space before AM/PM is optional)
TIMESTAMP_RE = re.compile(
    r"^\s*\w+,\s*(?P<month>\w+)\s+(?P<day>\d{1,2}),\s*(?P<year>\d{4})\s+at\s+"
    r"(?P<hour>\d{1,2}):(?P<minute>\d{2}):(?P<second>\d{2})\s*(?P<meridiem>[AaPp]\.?[Mm]\.?)\s*"
    r"(?P<tz>\S+)?\s*$"
)

# "10:15 PM", "10 : 00 PM", "11: 05 PM", "9:30 PM IST"
TIME_VALUE_RE = re.compile(
    r"(?P<hour>\d{1,2})\s*:\s*(?P<minute>\d{2})\s*(?P<meridiem>[AaPp]\.?[Mm]\.?)?"
)

_MONTHS = {
    m.casefold(): i
    for i, m in enumerate(
        [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ],
        start=1,
    )
}

# A session announcement always carries a work label; these phrases are how we
# recognise a *failed* announcement (one we should report rather than ignore).
ANNOUNCEMENT_HINT = re.compile(
    r"details for (?:today'?s|the) session|Reading Session", re.IGNORECASE
)


# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------


@dataclass
class WorkRef:
    """One work read in a session."""

    title: str
    author: str = ""

    @property
    def key(self) -> tuple[str, str]:
        return (self.title.casefold(), self.author.casefold())


@dataclass
class Session:
    message_id: str
    announced_by: str

    start: datetime
    end: datetime
    duration_minutes: int

    message_timestamp: datetime
    announced_date_raw: str = ""
    announced_time_raw: str = ""

    category: str = ""
    segment: str = ""
    primary: WorkRef | None = None
    additional_works: list[WorkRef] = field(default_factory=list)

    readers: list[str] = field(default_factory=list)
    readers_tentative: bool = False

    warnings: list[str] = field(default_factory=list)

    @property
    def works(self) -> list[WorkRef]:
        works = [self.primary] if self.primary else []
        return works + self.additional_works

    @property
    def title(self) -> str:
        return self.primary.title if self.primary else ""


# --------------------------------------------------------------------------
# Timestamp handling
# --------------------------------------------------------------------------


def parse_message_timestamp(value: str) -> datetime | None:
    """Parse the export's `created_date` string into an aware UTC datetime."""
    match = TIMESTAMP_RE.match(value or "")
    if not match:
        return None
    month = _MONTHS.get(match.group("month").casefold())
    if not month:
        return None

    hour = int(match.group("hour")) % 12
    if match.group("meridiem").replace(".", "").casefold() == "pm":
        hour += 12

    tz_name = (match.group("tz") or "UTC").upper()
    if tz_name not in {"UTC", "GMT"}:
        # The export has only ever contained UTC; anything else needs a look.
        return None

    return datetime(
        year=int(match.group("year")),
        month=month,
        day=int(match.group("day")),
        hour=hour,
        minute=int(match.group("minute")),
        second=int(match.group("second")),
        tzinfo=ZoneInfo("UTC"),
    )


def parse_announced_time(value: str) -> tuple[int, int] | None:
    """Pull (hour, minute) in 24h form out of an announced `Time :` value."""
    match = TIME_VALUE_RE.search(nz.clean(value))
    if not match:
        return None

    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    if hour > 23 or minute > 59:
        return None

    meridiem = (match.group("meridiem") or "").replace(".", "").casefold()
    if meridiem == "pm":
        hour = hour % 12 + 12
    elif meridiem == "am":
        hour = hour % 12
    # No meridiem given: the club has only ever met in the evening.
    elif hour < 8:
        hour += 12

    return hour, minute


def resolve_start(
    message_utc: datetime,
    announced_time: str,
    tz: ZoneInfo,
    warnings: list[str],
) -> datetime:
    """Work out when the session actually began.

    The announcement's own `Date :` line is unreliable - it carries copy-paste
    slips such as "09th, January, 2022" (meant 2023) and one post dated
    "29th May" that went out on 1st June. The message timestamp is always
    correct, so we take the *date* from the timestamp and the *time* from the
    announcement. No announcement in the export was posted after 18:30 UTC,
    so the local date can never roll over.
    """
    local = message_utc.astimezone(tz)
    parsed = parse_announced_time(announced_time)
    if not parsed:
        if announced_time.strip():
            warnings.append(f"unreadable Time value {announced_time.strip()!r}")
        return local

    hour, minute = parsed
    return local.replace(hour=hour, minute=minute, second=0, microsecond=0)


# --------------------------------------------------------------------------
# Work line handling
# --------------------------------------------------------------------------


def find_declared_author(text: str, config: Config) -> str:
    """Read a standalone "Writer :" / "Author :" line, if the post has one.

    Used when the work line itself carries no "by <Author>" - for example the
    January 2026 post that paired "Story : दो बैलों की कथा" with
    "Writer : मुंशी प्रेमचंद".
    """
    for field_name in config.author_fields:
        match = _field_pattern(field_name).search(text)
        if match:
            author = nz.normalize_author(match.group("value"), config)
            if author:
                return author
    return ""


def parse_work_line(value: str, config: Config) -> tuple[list[WorkRef], str, list[str]]:
    """Parse the text after "Book :" into works, a segment and extra activities.

    Handles three compound forms seen in the archive:
      "Salem's Lot + Ink What You Think"          -> work + club activity
      "Dagon and The Other Gods by X; Upper Berth by Y" -> two works
      "Lord of the Flies (Chapter 05)"            -> work + segment
    """
    text = nz.clean(value)
    works: list[WorkRef] = []
    activities: list[str] = []
    segment = ""

    for index, part in enumerate(p for p in text.split(";") if p.strip()):
        # "+" appends a club segment run alongside the reading.
        pieces = [p.strip() for p in part.split("+") if p.strip()]
        if not pieces:
            continue

        head, *extras = pieces
        activities.extend(nz.normalize_title(extra, config) for extra in extras)

        body, raw_segment = nz.split_segment(head, config)
        if raw_segment and index == 0 and not segment:
            segment = nz.normalize_segment(raw_segment)

        title_raw, author_raw = nz.split_title_author(body)
        title = nz.normalize_title(title_raw, config)
        author = nz.normalize_author(author_raw, config)

        if title and not title.lower().startswith(("http://", "https://")):
            works.append(WorkRef(title=title, author=author))

    return works, segment, [a for a in activities if a]


# --------------------------------------------------------------------------
# Message -> Session
# --------------------------------------------------------------------------


def parse_messages(messages: list[dict], config: Config) -> tuple[list[Session], list[dict]]:
    """Convert every announcement message into a Session.

    Returns (sessions, skipped) where `skipped` describes messages that looked
    like announcements but could not be parsed, so they can be reported.
    """
    label_re = _label_pattern(config.labels)
    tz = ZoneInfo(config.timezone_name)
    overrides = config.duration_overrides

    sessions: list[Session] = []
    skipped: list[dict] = []

    for message in messages:
        if not isinstance(message, dict):
            continue

        text = message.get("text") or ""
        if not text:
            continue

        label_match = label_re.search(text)
        if not label_match:
            if ANNOUNCEMENT_HINT.search(text) and TIME_RE.search(text):
                skipped.append(
                    {
                        "created_date": message.get("created_date", ""),
                        "reason": "announcement-like message with no Book/Story label",
                        "excerpt": nz.clean(text)[:160],
                    }
                )
            continue

        warnings: list[str] = []

        message_utc = parse_message_timestamp(message.get("created_date", ""))
        if message_utc is None:
            skipped.append(
                {
                    "created_date": message.get("created_date", ""),
                    "reason": "unparseable message timestamp",
                    "excerpt": nz.clean(text)[:160],
                }
            )
            continue

        works, segment, activities = parse_work_line(label_match.group("value"), config)

        # A separate "Writer :" line supplies the author when the title line omits it.
        if works and not works[0].author:
            declared = find_declared_author(text, config)
            if declared:
                works[0].author = declared

        if not works:
            skipped.append(
                {
                    "created_date": message.get("created_date", ""),
                    "reason": "no usable title on the work line",
                    "excerpt": nz.clean(label_match.group("value"))[:160],
                }
            )
            continue

        time_match = TIME_RE.search(text)
        date_match = DATE_RE.search(text)
        announced_time = time_match.group("value") if time_match else ""
        announced_date = nz.clean(date_match.group("value")) if date_match else ""

        start = resolve_start(message_utc, announced_time, tz, warnings)

        duration = overrides.get(start.date().isoformat(), config.default_duration)

        reader_match = READER_RE.search(text) or READERS_RE.search(text)
        raw_reader = reader_match.group("value") if reader_match else ""
        readers, tentative = nz.split_readers(raw_reader, config)

        if not reader_match:
            warnings.append("no Reader line in the announcement")
        elif not readers:
            warnings.append(f"reader not assigned ({nz.clean(raw_reader)!r})")

        # Club activities are recorded as works so nothing is lost; their type
        # in config/work_metadata.json marks them as non-literary.
        additional = works[1:] + [WorkRef(title=a) for a in activities]

        sessions.append(
            Session(
                message_id=message.get("message_id", ""),
                announced_by=nz.clean(message.get("creator", {}).get("name", "")),
                start=start,
                end=start + timedelta(minutes=duration),
                duration_minutes=duration,
                message_timestamp=message_utc,
                announced_date_raw=announced_date,
                announced_time_raw=nz.clean(announced_time),
                category=label_match.group("label").title(),
                segment=segment,
                primary=works[0],
                additional_works=additional,
                readers=readers,
                readers_tentative=tentative,
                warnings=warnings,
            )
        )

    sessions.sort(key=lambda s: s.start)
    return sessions, skipped

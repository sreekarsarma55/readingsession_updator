"""Generates a human-readable audit report of everything the pipeline was
unsure about, so the guesswork stays visible instead of hiding in the CSVs.
"""

from __future__ import annotations

from pathlib import Path

from .aggregate import Work
from .config import Config
from .outputs import iso_date
from .parsing import Session


def _section(lines: list[str], title: str) -> None:
    lines.append("")
    lines.append(f"## {title}")
    lines.append("")


def write_report(
    path: Path,
    sessions: list[Session],
    works: list[Work],
    skipped: list[dict],
    config: Config,
) -> Path:
    lines: list[str] = ["# Archive audit report", ""]

    total_minutes = sum(s.duration_minutes for s in sessions)
    unassigned = [s for s in sessions if not s.readers]
    tentative = [s for s in sessions if s.readers_tentative]
    missing_author = [w for w in works if not w.author and w.work_type != "Club Activity"]
    unverified = [w for w in works if w.confidence != "verified"]

    lines += [
        f"- Sessions parsed: **{len(sessions)}**",
        f"- Distinct works: **{len(works)}**",
        f"- Reading time (normalised): **{round(total_minutes / 60, 1)} hours**",
        f"- Date range: **{iso_date(sessions[0].start) if sessions else '-'}** "
        f"to **{iso_date(sessions[-1].start) if sessions else '-'}**",
    ]

    _section(lines, "Assumptions baked into the numbers")
    lines += [
        f"- The chat export never records how long a session ran, so every session "
        f"is normalised to **{config.default_duration} minutes** "
        f"(`default_duration_minutes` in `config/settings.json`).",
        "- `Stopped_At` is therefore `Created_Date + Duration_Minutes`, not an observed end time.",
        f"- `Created_Date` is the session's real start: the **date** comes from the message "
        f"timestamp and the **time** from the announcement's `Time :` line, resolved in "
        f"{config.settings.get('timezone_label', 'local time')} "
        f"({config.timezone_name}). The announcement's own `Date :` line is ignored because "
        "it contains copy-paste errors.",
        "- A co-read session stays one row, so `Duration_Minutes` is never double-counted.",
        "- `Hours` in `works.csv` credits each session to its primary work only.",
        "- Per-session corrections can be added to `duration_overrides` in `config/settings.json`.",
        "- `Stopped_At` is the site's live handover log, which narrators fill in each "
        "session, so it is exported **blank** for the history: a value inferred from a "
        "four-year-old announcement would read as something a human logged. What each "
        "session actually covered is already carried by `Segment`. Set "
        "`stopped_at_from_segment` to true to back-fill it anyway (it would reach only "
        "14 of the 217 rows).",
        "- The website's `duration_minutes` is nullable and the model says to leave it "
        "blank until recordings are measured. We fill it with the normalised value so the "
        "site's totals add up; set `emit_duration_minutes` to false to export it blank "
        "and keep that field strictly measured.",
    ]

    shared = [s for s in sessions if s.additional_works]
    if shared:
        _section(lines, "Works whose session count exceeds their session rows")
        lines += [
            "`sessions.csv` has one row per sitting, linked to that sitting's primary "
            "work. Where a single sitting covered two works, the second work's "
            "`Sessions` total in `works.csv` is higher than the number of rows naming "
            "it. Nothing is lost - the pairing is recorded in `Also_In_Session` in "
            "`sessions_detailed.csv`.",
            "",
        ]
        for session in shared:
            extras = "; ".join(w.title for w in session.additional_works)
            lines.append(f"- {iso_date(session.start)} - {session.title} + {extras}")

    renamed = sorted(
        w.title for w in works if w.title.endswith(")") and f"({w.author})" in w.title
    )
    if renamed:
        _section(lines, "Titles made unique for import")
        lines += [
            "Two works shared a title, which would break the website's lookup: "
            "`ReadingSession.work` is resolved by title, and `import_id_fields = "
            '("title",)` would fold them into one record. The author is appended to '
            "keep them distinct:",
            "",
        ]
        for title in renamed:
            lines.append(f"- {title}")

    if missing_author:
        _section(lines, f"Works still missing an author ({len(missing_author)})")
        for work in missing_author:
            note = f" - {work.note}" if work.note else ""
            lines.append(f"- **{work.title}** ({work.sessions} session(s)){note}")

    if unverified:
        _section(lines, f"Metadata needing a human check ({len(unverified)})")
        for work in unverified:
            note = f" - {work.note}" if work.note else ""
            lines.append(
                f"- **{work.title}** by {work.author or '?'} "
                f"[{work.confidence}]{note}"
            )

    uncertain_used = sorted(
        {
            name
            for session in sessions
            for name in session.readers
            if name.casefold() in config.reader_uncertain
        }
        | {
            config.reader_aliases.get(key, key)
            for key in config.reader_uncertain
            if key in config.reader_aliases
        }
    )
    if uncertain_used:
        _section(lines, "Reader identities that are educated guesses")
        lines.append(
            "These merges are set in `config/reader_aliases.json`. "
            "Confirm or correct them there:"
        )
        lines.append("")
        for key in sorted(config.reader_uncertain):
            target = config.reader_aliases.get(key)
            if target:
                lines.append(f"- `{key}` -> **{target}**")
            else:
                lines.append(f"- `{key}` -> left as-is, real name unknown")

    if unassigned:
        _section(lines, f"Sessions with no reader assigned ({len(unassigned)})")
        lines.append("The announcement said 'Open to all', 'Me', '???' or had no Reader line.")
        lines.append("")
        for session in unassigned:
            reason = "; ".join(session.warnings) or "no reader"
            lines.append(
                f"- {iso_date(session.start)} - {session.title} ({reason})"
            )

    if tentative:
        _section(lines, f"Sessions where the reader was still undecided ({len(tentative)})")
        for session in tentative:
            lines.append(
                f"- {iso_date(session.start)} - {session.title}: "
                f"{'; '.join(session.readers)}"
            )

    if skipped:
        _section(lines, f"Messages that looked like announcements but were skipped ({len(skipped)})")
        for item in skipped:
            lines.append(f"- {item['created_date']} - {item['reason']}")
            lines.append(f"  > {item['excerpt']}")

    _section(lines, "Multi-work and combined sessions")
    combined = [s for s in sessions if s.additional_works]
    if combined:
        for session in combined:
            extras = "; ".join(w.title for w in session.additional_works)
            lines.append(f"- {iso_date(session.start)} - {session.title} + {extras}")
    else:
        lines.append("_None._")

    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

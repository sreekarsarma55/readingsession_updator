"""Loads the JSON files in config/ into one object the rest of the pipeline reads.

Every piece of curated knowledge (title spellings, reader identities, authors,
session duration) lives in config/ so that fixing the data never means
editing the code.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "config"


def _load(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing config file: {path}")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _strip_comments(mapping: dict[str, Any]) -> dict[str, Any]:
    """Drop the `_comment`-style documentation keys used inside the config files."""
    return {k: v for k, v in mapping.items() if not k.startswith("_")}


@dataclass
class Config:
    settings: dict[str, Any]
    title_fixes: dict[str, str]
    author_fixes: dict[str, str]
    reader_aliases: dict[str, str]
    reader_uncertain: set[str]
    reader_separators: list[str]
    reader_tentative_markers: list[str]
    work_metadata: dict[str, dict[str, Any]]
    bad_readers: set[str]

    # Convenience accessors ------------------------------------------------
    labels: list[str] = field(default_factory=list)

    @property
    def timezone_name(self) -> str:
        return self.settings.get("timezone", "Asia/Kolkata")

    @property
    def default_duration(self) -> int:
        return int(self.settings.get("default_duration_minutes", 120))

    @property
    def duration_overrides(self) -> dict[str, int]:
        raw = self.settings.get("duration_overrides") or {}
        return {k: int(v) for k, v in raw.items()}

    @property
    def unassigned_label(self) -> str:
        return self.settings.get("unassigned_label", "Unassigned")

    @property
    def author_fields(self) -> list[str]:
        return self.settings.get("author_fields", ["Writer", "Author"])

    def site_category(self, announced_as: str) -> str:
        """Fold an announcement label onto the website's `category` vocabulary."""
        value = (announced_as or "").strip().casefold()
        mapping = {
            k.casefold(): v.casefold()
            for k, v in (self.settings.get("category_map") or {}).items()
        }
        return mapping.get(value, value)

    @property
    def segment_keywords(self) -> set[str]:
        return {w.casefold() for w in self.settings.get("segment_keywords", ["chapter"])}

    @property
    def output_dir(self) -> Path:
        return REPO_ROOT / self.settings.get("output_dir", "data/processed")

    @property
    def report_dir(self) -> Path:
        return REPO_ROOT / self.settings.get("report_dir", "data/reports")

    @property
    def source_file(self) -> Path:
        return REPO_ROOT / self.settings.get("source_file", "data/raw/messages.json")

    def work_meta(self, title: str, author: str = "") -> dict[str, Any]:
        """Look up curated metadata, preferring a `Title||Author` specific entry."""
        if author:
            specific = self.work_metadata.get(f"{title}||{author}".casefold())
            if specific:
                return specific
        return self.work_metadata.get(title.casefold(), {})


def load_config() -> Config:
    settings = _load("settings.json")
    titles = _strip_comments(_load("title_fixes.json"))
    authors = _strip_comments(_load("author_fixes.json"))
    readers_raw = _load("reader_aliases.json")
    works_raw = _strip_comments(_load("work_metadata.json"))

    aliases = {
        key.casefold(): value
        for key, value in _strip_comments(readers_raw.get("aliases", {})).items()
    }

    return Config(
        settings=settings,
        title_fixes={k.casefold(): v for k, v in titles.items()},
        author_fixes={k.casefold(): v for k, v in authors.items()},
        reader_aliases=aliases,
        reader_uncertain={x.casefold() for x in readers_raw.get("uncertain", [])},
        reader_separators=readers_raw.get("separators", ["/", "&", " and ", ","]),
        reader_tentative_markers=readers_raw.get("tentative_markers", []),
        work_metadata={k.casefold(): v for k, v in works_raw.items()},
        bad_readers={x.casefold() for x in settings.get("bad_readers", [])},
        labels=settings.get("labels", ["Book", "Story", "Novel", "Poem", "Piece"]),
    )

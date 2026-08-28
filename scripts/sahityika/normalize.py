"""Text tidying: turns messy chat strings into consistent titles, authors,
readers and segment labels.

The chat export carries a lot of incidental noise:
  * Google Chat / WhatsApp markdown  -> *Book*, _italics_, `code`
  * Unicode directional isolates     -> @\u2068Satyaki Goswami IITM\u2069
  * mention and contact prefixes      -> "@", "~", "@~"
  * non-breaking spaces inside names  -> "Satyaki\u00a0Goswami"
  * decorative quoting of titles      -> "The Last Leaf", 'Oh, Whistle...'
"""

from __future__ import annotations

import re
import unicodedata

from .config import Config


# Unicode directional isolate / formatting characters Google Chat wraps mentions in.
_INVISIBLE = dict.fromkeys(
    map(ord, "\u2066\u2067\u2068\u2069\u202a\u202b\u202c\u200e\u200f\u200b\ufeff")
)

_MARKDOWN = re.compile(r"[*_`~]")
_MULTISPACE = re.compile(r"\s+")

# A trailing "(...)" on a title: the chapter / canto / part that was read.
_TRAILING_PAREN = re.compile(r"\(([^()]*)\)\s*$")

# "<Title> by <Author>" - split on the first " by " only.
_BY = re.compile(r"\s+by\s+", re.IGNORECASE)
_LEADING_BY = re.compile(r"^(?:by\s+)+", re.IGNORECASE)

_CHAPTER_RANGE = re.compile(
    r"^chapters?\s*0*(\d+)\s*(?:-|–|—|to|&|and)\s*0*(\d+)$", re.IGNORECASE
)
_CHAPTER_ONE = re.compile(r"^chapters?\s*0*(\d+)$", re.IGNORECASE)

_PAIRED_QUOTES = [
    ('"', '"'),
    ("'", "'"),
    ("\u201c", "\u201d"),
    ("\u2018", "\u2019"),
]


def clean(text: str | None) -> str:
    """Strip markdown, invisible characters and redundant whitespace."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = text.translate(_INVISIBLE)
    text = _MARKDOWN.sub("", text)
    text = text.replace("\u00a0", " ")
    return _MULTISPACE.sub(" ", text).strip()


def strip_wrapping_quotes(text: str) -> str:
    """Remove decorative quotes that wrap a whole title.

    Only strips when the quote genuinely wraps the string, so an apostrophe
    inside a title (Salem's Lot) is never touched.
    """
    value = text.strip()
    changed = True
    while changed and len(value) >= 2:
        changed = False
        for opening, closing in _PAIRED_QUOTES:
            if value.startswith(opening) and value.endswith(closing):
                inner = value[len(opening) : -len(closing)].strip()
                # Refuse to strip if that would unbalance an inner quote.
                if inner:
                    value = inner
                    changed = True
                    break
    return value


def smart_case(text: str) -> str:
    """Gently de-shout ALL-CAPS strings, leaving mixed-case text alone."""
    letters = [c for c in text if c.isalpha()]
    if letters and all(c.isupper() for c in letters):
        return " ".join(word.capitalize() for word in text.split())
    return text


# --------------------------------------------------------------------------
# Titles, authors, segments
# --------------------------------------------------------------------------


def looks_like_segment(text: str, config: Config) -> bool:
    """True when a parenthetical names the portion read rather than the work.

    "(Chapter 05)" and "(Baal Kaand)" are segments; "(Dui Bondhu)", the Bengali
    title of Satyajit Ray's "The Promise", is part of the title itself.
    """
    value = text.strip()
    if not value:
        return False
    if any(ch.isdigit() for ch in value):
        return True
    words = {w.strip(".,-").casefold() for w in re.split(r"[\s\-]+", value)}
    return bool(words & config.segment_keywords)


def split_segment(title: str, config: Config) -> tuple[str, str]:
    """Separate a trailing parenthetical segment from the title.

    "Lord of the Flies (Chapter 05)" -> ("Lord of the Flies", "Chapter 05")
    "Ramayan(Baal Kaand)"            -> ("Ramayan", "Baal Kaand")
    "The Promise (Dui Bondhu)"       -> ("The Promise (Dui Bondhu)", "")
    """
    match = _TRAILING_PAREN.search(title)
    if not match:
        return title.strip(), ""

    segment = match.group(1).strip()
    remainder = title[: match.start()].strip()

    # A title that is *only* a parenthetical is not a segment at all.
    if not remainder:
        return title.strip(), ""

    if not looks_like_segment(segment, config):
        return title.strip(), ""

    return remainder, segment


def normalize_segment(segment: str) -> str:
    """Give chapter/part labels a single consistent shape."""
    value = clean(segment)
    if not value:
        return ""

    match = _CHAPTER_RANGE.match(value)
    if match:
        first, last = int(match.group(1)), int(match.group(2))
        if first == last:
            return f"Chapter {first}"
        return f"Chapters {first}-{last}"

    match = _CHAPTER_ONE.match(value)
    if match:
        return f"Chapter {int(match.group(1))}"

    # Non-numeric segments such as "Baal-Kaand" read better unhyphenated.
    if not any(ch.isdigit() for ch in value):
        value = value.replace("-", " ")
        value = _MULTISPACE.sub(" ", value).strip()

    return smart_case(value)


def handover_note(segment: str) -> str:
    """Derive a "where we stopped" note from the segment that was covered.

    The website's `stopped_at` is a note for whoever reads next, and the chat
    export never recorded one. The announced segment is the closest honest
    substitute: if a session covered Chapters 19-21, the next reader picks up
    after Chapter 21.

        "Chapters 19-21" -> "Chapter 21"
        "Chapter 5"      -> "Chapter 5"
        "Baal Kaand"     -> "Baal Kaand"
        ""               -> ""
    """
    value = (segment or "").strip()
    if not value:
        return ""

    match = re.match(
        r"^chapters?\s+(\d+)\s*(?:-|–|—|to)\s*(\d+)$", value, re.IGNORECASE
    )
    if match:
        return f"Chapter {int(match.group(2))}"

    return value


def split_title_author(text: str) -> tuple[str, str]:
    """Split "<Title> by <Author>" into its two halves.

    Tolerates the duplicated "by by" typo seen in the Little Prince posts.
    """
    parts = _BY.split(text, maxsplit=1)
    if len(parts) == 1:
        return text.strip(), ""
    title, author = parts[0].strip(), parts[1].strip()
    author = _LEADING_BY.sub("", author).strip()
    return title, author


def normalize_title(raw: str, config: Config) -> str:
    value = strip_wrapping_quotes(clean(raw))
    value = value.strip(" .,;:-\u2013\u2014")
    if not value:
        return ""
    fixed = config.title_fixes.get(value.casefold())
    if fixed:
        return fixed
    return smart_case(value)


def normalize_author(raw: str, config: Config) -> str:
    value = strip_wrapping_quotes(clean(raw))
    value = _LEADING_BY.sub("", value)
    value = value.strip(" .,;:-\u2013\u2014")
    if not value:
        return ""
    fixed = config.author_fixes.get(value.casefold())
    if fixed:
        return fixed
    return smart_case(value)


# --------------------------------------------------------------------------
# Readers
# --------------------------------------------------------------------------

_MENTION_PREFIX = re.compile(r"^[@~\s]+")
_IITM_SUFFIX = re.compile(r"\s+IITM$", re.IGNORECASE)


def _canonical_reader(raw: str, config: Config) -> str:
    value = clean(raw)
    value = _MENTION_PREFIX.sub("", value)
    value = _IITM_SUFFIX.sub("", value).strip()
    value = value.strip(" .,;:/&-")
    if not value:
        return ""

    key = value.casefold()
    if key in config.bad_readers:
        return ""

    alias = config.reader_aliases.get(key)
    if alias:
        return alias
    return smart_case(value)


def split_readers(raw: str, config: Config) -> tuple[list[str], bool]:
    """Turn one Reader: line into an ordered, de-duplicated list of people.

    Returns (readers, tentative) where `tentative` marks announcements that
    said something like "A and/or B or C" - i.e. it was still being decided.
    """
    text = clean(raw)
    if not text:
        return [], False

    # Match the markers verbatim - stripping " or " down to "or" would match the
    # "or" inside surnames like Chakraborty and Rathore.
    padded = f" {text} ".casefold()
    tentative = any(
        marker.casefold() in padded
        for marker in config.reader_tentative_markers
        if marker
    )

    chunks = [text]
    for separator in config.reader_separators:
        nxt: list[str] = []
        for chunk in chunks:
            if separator.strip():
                nxt.extend(re.split(re.escape(separator), chunk, flags=re.IGNORECASE))
            else:
                nxt.append(chunk)
        chunks = nxt

    readers: list[str] = []
    for chunk in chunks:
        name = _canonical_reader(chunk, config)
        if name and name not in readers:
            readers.append(name)

    return readers, tentative

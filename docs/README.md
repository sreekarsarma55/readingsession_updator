# Sahityika Reading Archive

Turns the club's Google Chat export into a tidy, sorted record of every reading
session: what was read, who read it, when, and for how long.

## Build it

```bash
python3 scripts/build.py
```

No dependencies beyond the Python standard library (3.9+). Options:

```bash
python3 scripts/build.py --source data/raw/oldmessages.json   # a different export
python3 scripts/build.py --duration 90                        # different normalised length
python3 scripts/build.py --out /tmp/out                       # write elsewhere
```

## Layout

```
config/              curated knowledge - edit these, not the code
data/raw/            original chat exports
data/processed/      generated CSV + JSON
data/reports/        audit.md, listing everything the build was unsure about
scripts/build.py     entry point
scripts/sahityika/   pipeline modules
scripts/archive/     superseded one-off scripts, kept for reference
```

## What gets generated

| File | One row per | Purpose |
|---|---|---|
| `sessions.csv` | session | The core log: `Title, Reader, Segment, Created_Date, Stopped_At, Duration_Minutes` |
| `sessions_detailed.csv` | session | Same sessions plus author, category, announcer, raw announcement values, warnings |
| `works.csv` | work | Everything read, most-read first. Import-ready for the website (see below) |
| `club_activities.csv` | activity | The club's own segments, kept out of the reading list |
| `work_readers.csv` | work | Just the work and everyone who read it, alphabetical |
| `readers.csv` | person | Session and hour totals per reader |
| `authors.csv` | author | Works and sessions per author |
| `timeline.csv` | work | Works in the order the club started them |
| `archive.json` | – | Full structured dump of sessions and works |

## Importing works.csv into the website

`works.csv` is shaped for the Django admin importer at
`/admin/web/readingwork/import/`. Its first nine columns use the exact names and
order the `ReadingWork` importer expects:

```
Title, Author, Category, Actual_Type, Language, Country, Sessions, First_Date, Last_Date
```

Everything after `Last_Date` (`Hours`, `Reader_Count`, `Readers`,
`Segments_Covered`, `Author_Confidence`, `Notes`) is extra context for humans —
the importer ignores columns it does not recognise.

Column names here are the importer's, which differ from the model's own field
names — the resource renames them:

| CSV column | `ReadingWork` field |
|---|---|
| `Actual_Type` | `work_type` |
| `Sessions` | `legacy_session_count` |
| `First_Date` | `first_read_on` |
| `Last_Date` | `last_read_on` |

Details worth knowing:

- **`Category` is lower-cased and folded onto `CATEGORY_CHOICES`**
  (`book`, `novel`, `story`, `piece`, `poem`, `other`). The club has used
  interchangeable labels over the years, so `category_map` in
  `config/settings.json` maps `tale → story`, `novella → novel` and so on.
  Without it, recovering the March–May 2025 `Tale :` sessions would push an
  invalid `tale` value at a choices-validated field.
- **`Status`** uses `STATUS_CHOICES` and defaults to `completed`. The book
  currently being read is set in `status_overrides` in `config/settings.json`.
  The site allows only one work in `reading`, so keep that to a single entry.
- **`Genre`** is free text (`CharField`, 120 chars), curated in
  `config/genres.json`. It is filled for 55 of 64 works; anything genuinely
  mixed, unattributed, or a member's own piece is left blank on purpose, since
  a wrong genre on a public page is worse than an empty one.
- **`Last_Date` matters for site ordering.** `ReadingWork.Meta.ordering` is
  `["-last_read_on", "-created_at"]`, so while this column was empty the
  reading list fell back to creation order.
- **Club segments are not in `works.csv`.** *From The Pages of Childhood* and
  *Ink What You Think* ran alongside readings but are not published works, so
  they go to `club_activities.csv`. Import them only if you want them listed,
  and use category `other`.

### Re-importing without creating duplicates

The import preview marks every row `New` because the CSV carries no primary key,
and `django-import-export` matches on `id` by default. Re-importing therefore
appends a second copy of every work rather than updating it. Set the resource to
match on the title instead:

```python
class ReadingWorkResource(resources.ModelResource):
    class Meta:
        model = ReadingWork
        import_id_fields = ("title",)
```

With that in place, re-running the import updates existing rows and only genuine
additions show up as `New`.

## How the numbers are derived

**`Created_Date` is the session's start time.** The date comes from the message
timestamp and the time from the announcement's `Time :` line, resolved in IST.
The announcement's own `Date :` line is deliberately ignored because it carries
copy-paste slips — one post is dated "09th, January, 2022" when it meant 2023,
and another says "29th May" but went out on 1st June.

**`Duration_Minutes` is normalised, not measured.** The export never records how
long a session ran, so every session is credited with
`default_duration_minutes` (120) from `config/settings.json`.
`Stopped_At` is simply `Created_Date + Duration_Minutes`. If you know specific
sessions ran longer or shorter, add them to `duration_overrides`:

```json
"duration_overrides": { "2025-03-17": 90 }
```

**A co-read session stays one row.** When two people share a session the Reader
cell lists both, so `Duration_Minutes` is never double-counted. `Hours` in
`works.csv` credits each session to its primary work only, which means the
column sums to the true total programme time.

**`Segment`** is the portion read, lifted from the trailing parenthesis and
normalised (`(Chapter 05)` → `Chapter 5`, `(Chapter 19-21)` → `Chapters 19-21`).
A parenthesis is only treated as a segment when it contains a digit or a word
like *chapter* or *kaand* — so *The Promise (Dui Bondhu)*, where the bracket
holds the original Bengali title, is left intact.

## Editing the data

All curated knowledge lives in `config/`, so correcting the archive never means
touching code:

| File | Holds |
|---|---|
| `settings.json` | Duration, timezone, work labels, bad reader values, category map, status |
| `genres.json` | Genre per work, for the website's `genre` field |
| `title_fixes.json` | Canonical spellings (`Carmila` → `Carmilla`) |
| `author_fixes.json` | Canonical author names (`H.P Lovecraft` → `H. P. Lovecraft`) |
| `reader_aliases.json` | Reader identity merges, multi-reader separators |
| `work_metadata.json` | Author, type, language, country and notes per work |

After every build, read `data/reports/audit.md`. It lists unresolved authors,
reader merges that are educated guesses, sessions with no reader assigned, and
any announcement-shaped message the parser skipped.

## Parser notes

Announcements are wildly inconsistent, so the parser tolerates:

- markdown either side of the colon — `Book : X`, `*Book* : *X*`, `*Book : X*`
- nine different work labels; the club used `Tale :` exclusively from March to
  May 2025 and `Book :` most other times
- a separate `Writer :` / `Author :` line instead of `Title by Author`
- combined sessions — `Salem's Lot + Ink What You Think` (work plus club
  segment) and `Dagon ... by X; The Upper Berth by Y` (two works, one meeting)
- reader lists split by `/`, `&`, `and`, `or`, `and/or`
- Google Chat mention wrappers, non-breaking spaces and `@`/`~` prefixes
- two distinct works that share the title *Submission*, told apart by author

Sessions with no book at all — the Independence Day special, a discussion-only
night, an open mic — are intentionally excluded and listed in the audit report.

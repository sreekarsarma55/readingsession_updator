import json
import re
import csv
from collections import defaultdict

INPUT_FILE = "messages.json"

# =====================================================
# LOAD
# =====================================================

with open(INPUT_FILE, encoding="utf-8") as f:
    raw = json.load(f)

messages = raw.get("messages", [])

print(f"Loaded {len(messages)} messages")

# =====================================================
# NORMALIZATION
# =====================================================

TITLE_FIXES = {
    "Carmila": "Carmilla",
    "The Murder of Roger Ackyord":
        "The Murder of Roger Ackroyd",
}

BAD_READERS = {
    "",
    "Open",
    "Open to all",
    "open to all",
    "???",
    "Me",
    "To be decided in the session",
}

READER_ALIASES = {
    "Satyaki Goswami IITM":
        "Satyaki Goswami",
}

# =====================================================
# HELPERS
# =====================================================

def clean(text):

    if not text:
        return ""

    text = re.sub(r'[*_`]', '', text)
    text = re.sub(r'@⁨|⁩', '', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def normalize_title(title):

    title = clean(title)

    # remove chapter info
    title = re.sub(
        r'\s*\(.*?chapter.*?\)',
        '',
        title,
        flags=re.I
    )

    # split accidental merged titles
    if "+" in title:
        title = title.split("+")[0]

    title = title.strip()

    title = TITLE_FIXES.get(title, title)

    return title


def normalize_reader(reader):

    reader = clean(reader)

    if reader in BAD_READERS:
        return ""

    return READER_ALIASES.get(reader, reader)


def extract_title(text):

    patterns = [
        r'Book\s*:\s*(.+)',
        r'Novel\s*:\s*(.+)',
        r'Story\s*:\s*(.+)',
        r'Piece\s*:\s*(.+)',
        r'Poem\s*:\s*(.+)',
    ]

    for pattern in patterns:

        m = re.search(
            pattern,
            text,
            re.I
        )

        if m:

            title = m.group(1)

            title = title.split("\n")[0]

            title = re.split(
                r'Reader\s*:|Link\s*:',
                title,
                flags=re.I
            )[0]

            title = clean(title)

            return title

    return None


def extract_author_and_title(title):

    m = re.search(
        r'(.+?)\s+by\s+(.+)',
        title,
        re.I
    )

    if not m:
        return "", normalize_title(title)

    work = normalize_title(
        m.group(1)
    )

    author = clean(
        m.group(2)
    )

    return author, work


def extract_reader(text):

    m = re.search(
        r'Reader\s*:\s*(.+)',
        text,
        re.I
    )

    if not m:
        return ""

    reader = m.group(1)

    reader = reader.split("\n")[0]

    return normalize_reader(reader)


def extract_category(text):

    categories = {
        "Book": r'Book\s*:',
        "Novel": r'Novel\s*:',
        "Story": r'Story\s*:',
        "Piece": r'Piece\s*:',
        "Poem": r'Poem\s*:'
    }

    for name, pattern in categories.items():

        if re.search(
            pattern,
            text,
            re.I
        ):
            return name

    return "Unknown"


# =====================================================
# STORAGE
# =====================================================

sessions = []

works = defaultdict(lambda: {
    "title": "",
    "author": "",
    "category": "",
    "sessions": 0,
    "readers": set(),
    "first_date": "",
    "last_date": ""
})

reader_stats = defaultdict(int)
author_stats = defaultdict(int)

# =====================================================
# EXTRACT
# =====================================================

for msg in messages:

    if not isinstance(msg, dict):
        continue

    text = msg.get("text", "")

    if not text:
        continue

    raw_title = extract_title(text)

    if not raw_title:
        continue

    author, title = extract_author_and_title(
        raw_title
    )

    if title.startswith("http"):
        continue

    category = extract_category(text)

    reader = extract_reader(text)

    created_date = msg.get(
        "created_date",
        ""
    )

    creator = (
        msg.get("creator", {})
        .get("name", "")
    )

    sessions.append({
        "title": title,
        "author": author,
        "reader": reader,
        "category": category,
        "date": created_date,
        "creator": creator,
    })

    key = title.lower()

    works[key]["title"] = title
    works[key]["author"] = author
    works[key]["category"] = category
    works[key]["sessions"] += 1

    if reader:
        works[key]["readers"].add(reader)
        reader_stats[reader] += 1

    if author:
        author_stats[author] += 1

    if not works[key]["first_date"]:
        works[key]["first_date"] = created_date

    works[key]["last_date"] = created_date

# =====================================================
# SAVE WORKS
# =====================================================

with open(
    "works.csv",
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "Title",
        "Author",
        "Category",
        "Sessions",
        "Readers",
        "First_Date",
        "Last_Date"
    ])

    for work in sorted(
        works.values(),
        key=lambda x: x["sessions"],
        reverse=True
    ):

        writer.writerow([
            work["title"],
            work["author"],
            work["category"],
            work["sessions"],
            "; ".join(
                sorted(work["readers"])
            ),
            work["first_date"],
            work["last_date"]
        ])

# =====================================================
# SAVE READERS
# =====================================================

with open(
    "readers.csv",
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "Reader",
        "Sessions"
    ])

    for reader, count in sorted(
        reader_stats.items(),
        key=lambda x: x[1],
        reverse=True
    ):

        writer.writerow([
            reader,
            count
        ])

# =====================================================
# SAVE AUTHORS
# =====================================================

with open(
    "authors.csv",
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "Author",
        "Sessions"
    ])

    for author, count in sorted(
        author_stats.items(),
        key=lambda x: x[1],
        reverse=True
    ):

        writer.writerow([
            author,
            count
        ])

# =====================================================
# SAVE ARCHIVE
# =====================================================

with open(
    "archive.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        sessions,
        f,
        indent=2,
        ensure_ascii=False
    )

# =====================================================
# REPORT
# =====================================================

print("\n" + "=" * 60)
print("SAHITYIKA ARCHIVE REPORT")
print("=" * 60)

print(f"Messages scanned : {len(messages)}")
print(f"Sessions found   : {len(sessions)}")
print(f"Unique works     : {len(works)}")

print("\nTOP 20 WORKS\n")

for work in sorted(
    works.values(),
    key=lambda x: x["sessions"],
    reverse=True
)[:20]:

    print(
        f"{work['sessions']:>3} | {work['title']}"
    )

print("\nGenerated:")
print("✓ works.csv")
print("✓ readers.csv")
print("✓ authors.csv")
print("✓ archive.json")
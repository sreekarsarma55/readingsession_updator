import json
import re
import csv
from collections import defaultdict

INPUT_FILE = "messages.json"

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    raw = json.load(f)

data = raw.get("messages", [])

print(f"Loaded {len(data)} messages")

# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------

def clean_text(text):
    if not text:
        return ""

    text = re.sub(r'[*_`]', '', text)
    text = re.sub(r'@⁨|⁩', '', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def extract_title(text):

    patterns = [
        r'Book\s*:\s*(.+)',
        r'Novel\s*:\s*(.+)',
        r'Story\s*:\s*(.+)',
        r'Piece\s*:\s*(.+)',
        r'Poem\s*:\s*(.+)',
    ]

    for pattern in patterns:

        match = re.search(pattern, text, re.IGNORECASE)

        if match:

            title = match.group(1)

            title = title.split("\n")[0]

            title = re.split(
                r'Reader\s*:|Link\s*:',
                title,
                flags=re.IGNORECASE
            )[0]

            return clean_text(title)

    return None


def extract_category(text):

    mapping = {
        "Book": r'Book\s*:',
        "Novel": r'Novel\s*:',
        "Story": r'Story\s*:',
        "Piece": r'Piece\s*:',
        "Poem": r'Poem\s*:'
    }

    for category, pattern in mapping.items():
        if re.search(pattern, text, re.IGNORECASE):
            return category

    return "Unknown"


def extract_reader(text):

    match = re.search(
        r'Reader\s*:\s*(.+)',
        text,
        re.IGNORECASE
    )

    if not match:
        return ""

    reader = match.group(1)

    reader = reader.split("\n")[0]

    return clean_text(reader)


# ---------------------------------------------------
# STORAGE
# ---------------------------------------------------

sessions = []

works = defaultdict(lambda: {
    "title": "",
    "category": "",
    "sessions": 0,
    "readers": set(),
    "first_date": "",
    "last_date": ""
})

# ---------------------------------------------------
# PARSE
# ---------------------------------------------------

for msg in data:

    if not isinstance(msg, dict):
        continue

    text = msg.get("text", "")

    if not text:
        continue

    # skip obvious noise
    if text in [
        "Updated room membership.",
        "Created room.",
        "Renamed room."
    ]:
        continue

    title = extract_title(text)

    if not title:
        continue

    category = extract_category(text)
    reader = extract_reader(text)

    created_date = msg.get("created_date", "")
    creator = msg.get("creator", {}).get("name", "")

    sessions.append({
        "title": title,
        "category": category,
        "reader": reader,
        "created_date": created_date,
        "creator": creator,
    })

    key = title.lower()

    works[key]["title"] = title
    works[key]["category"] = category
    works[key]["sessions"] += 1

    if reader:
        works[key]["readers"].add(reader)

    if not works[key]["first_date"]:
        works[key]["first_date"] = created_date

    works[key]["last_date"] = created_date

# ---------------------------------------------------
# SAVE SESSIONS
# ---------------------------------------------------

with open(
    "sessions.csv",
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "Title",
        "Category",
        "Reader",
        "Created_Date",
        "Creator"
    ])

    for s in sessions:

        writer.writerow([
            s["title"],
            s["category"],
            s["reader"],
            s["created_date"],
            s["creator"]
        ])

# ---------------------------------------------------
# SAVE WORKS
# ---------------------------------------------------

with open(
    "works.csv",
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "Title",
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
            work["category"],
            work["sessions"],
            "; ".join(sorted(work["readers"])),
            work["first_date"],
            work["last_date"]
        ])

# ---------------------------------------------------
# QUICK REPORT
# ---------------------------------------------------

print("\n" + "=" * 60)
print("SAHITYIKA ARCHIVE REPORT")
print("=" * 60)

print(f"Messages scanned : {len(data)}")
print(f"Sessions found   : {len(sessions)}")
print(f"Unique works     : {len(works)}")

print("\nTOP WORKS\n")

for work in sorted(
    works.values(),
    key=lambda x: x["sessions"],
    reverse=True
)[:20]:

    print(
        f"{work['sessions']:>3} | {work['title']}"
    )

print("\nFiles generated:")
print("✓ sessions.csv")
print("✓ works.csv")
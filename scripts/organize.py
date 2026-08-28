import os
import shutil

ROOT = "sahityika-archive"

# =====================================================
# CREATE FOLDERS
# =====================================================

dirs = [
    f"{ROOT}/data/raw",
    f"{ROOT}/data/processed",
    f"{ROOT}/data/reports",
    f"{ROOT}/scripts",
    f"{ROOT}/docs",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# =====================================================
# FILES TO MOVE
# =====================================================

moves = {
    # raw
    "messages.json":
        f"{ROOT}/data/raw/messages.json",

    # processed
    "archive.json":
        f"{ROOT}/data/processed/archive.json",

    "sessions.csv":
        f"{ROOT}/data/processed/sessions.csv",

    "works.csv":
        f"{ROOT}/data/processed/works.csv",

    "works_enriched.csv":
        f"{ROOT}/data/processed/works_enriched.csv",

    "readers.csv":
        f"{ROOT}/data/processed/readers.csv",

    "authors.csv":
        f"{ROOT}/data/processed/authors.csv",

    "timeline.csv":
        f"{ROOT}/data/processed/timeline.csv",

    # scripts
    "extractor.py":
        f"{ROOT}/scripts/extractor.py",

    "v5.py":
        f"{ROOT}/scripts/v5.py",

    "audit.py":
        f"{ROOT}/scripts/audit.py",

    "enrich.py":
        f"{ROOT}/scripts/enrich.py",

    "timeline.py":
        f"{ROOT}/scripts/timeline.py",
}

# =====================================================
# MOVE FILES
# =====================================================

for src, dst in moves.items():

    if os.path.exists(src):

        try:
            shutil.move(src, dst)
            print(f"Moved: {src}")

        except Exception as e:
            print(f"Could not move {src}: {e}")

# =====================================================
# README
# =====================================================

readme = f"{ROOT}/docs/README.md"

if not os.path.exists(readme):

    with open(readme, "w", encoding="utf-8") as f:

        f.write(
"""# Sahityika Reading Archive

Generated from Google Chat exports.

## Structure

data/raw
    Original exports

data/processed
    Generated archive files

scripts
    Processing scripts

docs
    Metadata and notes
"""
        )

# =====================================================
# TITLE FIXES
# =====================================================

title_fixes = f"{ROOT}/docs/title_fixes.json"

if not os.path.exists(title_fixes):

    with open(title_fixes, "w", encoding="utf-8") as f:

        f.write(
"""{
  "Carmila": "Carmilla",
  "The Murder of Roger Ackyord": "The Murder of Roger Ackroyd"
}
"""
        )

# =====================================================
# KNOWN AUTHORS
# =====================================================

known_authors = f"{ROOT}/docs/known_authors.json"

if not os.path.exists(known_authors):

    with open(known_authors, "w", encoding="utf-8") as f:

        f.write(
"""{
  "Salem's Lot": "Stephen King",
  "Hellstar Remina": "Junji Ito",
  "Lord of the Flies": "William Golding",
  "The Murder of Roger Ackroyd": "Agatha Christie",
  "Uglies": "Scott Westerfeld"
}
"""
        )

print()
print("=" * 50)
print("Archive structure created.")
print(f"Location: ./{ROOT}")
print("=" * 50)
import csv
import json

KNOWN_WORKS = {

    "Salem's Lot": {
        "author": "Stephen King",
        "type": "Novel",
        "country": "USA",
        "language": "English"
    },

    "Waiting For The Mahatma": {
        "author": "R. K. Narayan",
        "type": "Novel",
        "country": "India",
        "language": "English"
    },

    "Devolution": {
        "author": "Max Brooks",
        "type": "Novel",
        "country": "USA",
        "language": "English"
    },

    "The Murder of Roger Ackroyd": {
        "author": "Agatha Christie",
        "type": "Novel",
        "country": "United Kingdom",
        "language": "English"
    },

    "The Strangest Man": {
        "author": "Graham Farmelo",
        "type": "Biography",
        "country": "United Kingdom",
        "language": "English"
    },

    "Hellstar Remina": {
        "author": "Junji Ito",
        "type": "Manga",
        "country": "Japan",
        "language": "Japanese"
    },

    "Lord of the Flies": {
        "author": "William Golding",
        "type": "Novel",
        "country": "United Kingdom",
        "language": "English"
    },

    "Uglies": {
        "author": "Scott Westerfeld",
        "type": "Novel",
        "country": "USA",
        "language": "English"
    },

    "Carmilla": {
        "author": "Sheridan Le Fanu",
        "type": "Novella",
        "country": "Ireland",
        "language": "English"
    },

    "Rashmirathi": {
        "author": "Ramdhari Singh Dinkar",
        "type": "Epic Poem",
        "country": "India",
        "language": "Hindi"
    },

    "The Kite Runner": {
        "author": "Khaled Hosseini",
        "type": "Novel",
        "country": "Afghanistan",
        "language": "English"
    },

    "Pride & Prejudice": {
        "author": "Jane Austen",
        "type": "Novel",
        "country": "United Kingdom",
        "language": "English"
    }
}

metadata = {}
missing = []

with open(
    "../data/processed/works.csv",
    encoding="utf-8"
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        title = row["Title"]

        if title in KNOWN_WORKS:

            metadata[title] = {
                **KNOWN_WORKS[title],
                "status": "auto"
            }

        else:

            metadata[title] = {
                "author": "TODO",
                "type": "TODO",
                "country": "TODO",
                "language": "TODO",
                "status": "manual"
            }

            missing.append(title)

with open(
    "../docs/work_metadata.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        metadata,
        f,
        indent=2,
        ensure_ascii=False
    )

print()
print("=" * 60)
print("METADATA REPORT")
print("=" * 60)

print(f"Total works : {len(metadata)}")
print(f"Auto-filled : {len(metadata) - len(missing)}")
print(f"Missing     : {len(missing)}")

if missing:

    print("\nMANUAL REVIEW NEEDED:\n")

    for title in missing:
        print("-", title)

print()
print("Saved:")
print("../docs/work_metadata.json")
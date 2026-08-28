import csv

KNOWN_WORKS = {

    "Salem's Lot": (
        "Stephen King",
        "Novel"
    ),

    "Waiting For The Mahatma": (
        "R. K. Narayan",
        "Novel"
    ),

    "The Murder of Roger Ackroyd": (
        "Agatha Christie",
        "Novel"
    ),

    "Hellstar Remina": (
        "Junji Ito",
        "Manga"
    ),

    "Lord of the Flies": (
        "William Golding",
        "Novel"
    ),

    "Uglies": (
        "Scott Westerfeld",
        "Novel"
    ),

    "The Strangest Man": (
        "Graham Farmelo",
        "Biography"
    ),

    "Rashmirathi": (
        "Ramdhari Singh Dinkar",
        "Epic Poem"
    ),

    "Carmilla": (
        "Sheridan Le Fanu",
        "Novella"
    ),

    "The Wendigo": (
        "Algernon Blackwood",
        "Novella"
    ),

    "The Monkey's Paw": (
        "W. W. Jacobs",
        "Short Story"
    ),
}

rows = []

with open(
    "works.csv",
    encoding="utf-8"
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        title = row["Title"]

        if title in KNOWN_WORKS:

            author, actual_type = KNOWN_WORKS[title]

            if not row["Author"]:
                row["Author"] = author

            row["Actual_Type"] = actual_type

        else:

            row["Actual_Type"] = row["Category"]

        rows.append(row)

fieldnames = list(rows[0].keys())

if "Actual_Type" not in fieldnames:
    fieldnames.append("Actual_Type")

with open(
    "works_enriched.csv",
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()

    for row in rows:
        writer.writerow(row)

print(
    f"Enriched {len(rows)} works"
)
print(
    "Saved -> works_enriched.csv"
)
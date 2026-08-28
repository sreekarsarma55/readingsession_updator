import json
import csv
from collections import defaultdict

with open(
    "archive.json",
    encoding="utf-8"
) as f:

    sessions = json.load(f)

timeline = defaultdict(
    lambda: {
        "first": "",
        "last": "",
        "count": 0
    }
)

for s in sessions:

    title = s["title"]

    date = s["date"]

    timeline[title]["count"] += 1

    if (
        timeline[title]["first"] == ""
        or date < timeline[title]["first"]
    ):
        timeline[title]["first"] = date

    if (
        timeline[title]["last"] == ""
        or date > timeline[title]["last"]
    ):
        timeline[title]["last"] = date

with open(
    "timeline.csv",
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "Title",
        "First_Date",
        "Last_Date",
        "Sessions"
    ])

    for title, info in sorted(
        timeline.items(),
        key=lambda x: x[1]["count"],
        reverse=True
    ):

        writer.writerow([
            title,
            info["first"],
            info["last"],
            info["count"]
        ])

print(
    f"Generated timeline for {len(timeline)} works"
)
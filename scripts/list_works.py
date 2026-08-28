import csv

with open(
    "../data/processed/works.csv",
    encoding="utf-8"
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        print(row["Title"])
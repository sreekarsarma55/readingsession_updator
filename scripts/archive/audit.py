import json

with open("messages.json", encoding="utf-8") as f:
    data = json.load(f)["messages"]

TARGET = "Hellstar Remina"

for msg in data:

    text = msg.get("text", "")

    if TARGET.lower() in text.lower():

        print("=" * 80)
        print(msg.get("created_date"))
        print(text[:1000])
"""Sahityika reading-session archive pipeline.

Turns the raw Google Chat export in data/raw/ into a set of tidy,
sorted CSV files in data/processed/.

Run it with:  python3 scripts/build.py
"""

__all__ = [
    "config",
    "normalize",
    "parsing",
    "aggregate",
    "outputs",
]

"""Freeze the train/test split once: stratified random 80/20, seed 42.

Run from anywhere: python work/exploration/prepare_split.py
Never re-run it after looking at results.
"""
import json
from datetime import date
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SEED = 42
TEST_SIZE = 0.2

if (OUT / "test.csv").exists():
    raise SystemExit("test.csv already exists: the split is frozen. Delete it only if you know why.")

df = pd.read_csv(ROOT / "data" / "bank_10k.csv")
train, test = train_test_split(df, test_size=TEST_SIZE, stratify=df["y"], random_state=SEED)
train = train.sort_values("contact_order")
test = test.sort_values("contact_order")

# Checks from the guideline §4.6
assert len(train) + len(test) == len(df)
assert set(train["contact_order"]).isdisjoint(test["contact_order"])
rate = lambda d: float((d["y"] == "yes").mean())
assert abs(rate(train) - rate(test)) < 0.01

train.to_csv(OUT / "train.csv", index=False)
test.to_csv(OUT / "test.csv", index=False)
meta = {
    "source": "data/bank_10k.csv",
    "method": "stratified random (on y)",
    "test_size": TEST_SIZE,
    "seed": SEED,
    "date": date.today().isoformat(),
    "n_source": len(df),
    "n_train": len(train),
    "n_test": len(test),
    "rate_source": rate(df),
    "rate_train": rate(train),
    "rate_test": rate(test),
    "note": "Rows drift strongly over contact_order (see EDA §6); a random split mixes periods, so test profit is likely optimistic for a future campaign.",
}
(OUT / "split_metadata.json").write_text(json.dumps(meta, indent=2))
print(json.dumps(meta, indent=2))

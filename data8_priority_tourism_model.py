"""DATA 8.2: curated, checked 18-attraction planning lot.

A named candidate at Cologne/Ghent has NO canonical attraction ID and cannot
silently become a wishlist item or appear as an approved catalog attraction.
"""
from pathlib import Path
from data8_attraction_evidence_model import load_dataset, coverage_report

DATA = Path(__file__).resolve().parent / "data" / "data8_priority_tourism_2026_11.json"

def load_priority_lot(*, discovery=None):
    return load_dataset(DATA, discovery=discovery)

def lot_coverage(*, discovery=None):
    return coverage_report(load_priority_lot(discovery=discovery))

"""Integration tests for the Phase 0-4 pipeline invariants.

Run with: pytest tests/ (from the project root, with .venv activated).
These check structural invariants of the already-generated data files, not
network access or PDF re-extraction (that would make tests slow/flaky and
dependent on external sites staying up). Re-run the src/ scripts first if
data/ is stale or missing.
"""
import csv
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_source_manifest_checksums_match_files():
    manifest_path = ROOT / "source_manifest.csv"
    assert manifest_path.exists(), "run src/build_manifest.py first"
    rows = list(csv.DictReader(open(manifest_path, encoding="utf-8")))
    assert len(rows) >= 12
    for row in rows:
        path = ROOT / row["relative_path"]
        assert path.exists(), f"manifest references missing file: {path}"
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        assert h.hexdigest() == row["sha256"], f"checksum mismatch: {path}"
        assert int(row["file_size_bytes"]) == path.stat().st_size


def test_kde_pdf_extraction_page_count():
    data = json.loads((ROOT / "data/interim/kde_modell_test_extracted.json").read_text())
    assert len(data) == 24, "official model test is documented as 24 pages"
    assert "Kanton Zürich" in data[0]["text"]


def test_kde_section_map_covers_all_documented_pages():
    df = pd.read_csv(ROOT / "data/interim/kde_model_test_section_map.csv")
    model_test_pages = set(df[df["doc"] == "model_test"]["page"])
    assert model_test_pages == set(range(1, 25))
    # every content page (not metadata) must have a non-null description
    assert df["description"].notna().all()


def test_goethe_extraction_produced_all_three_levels():
    df = pd.read_csv(ROOT / "data/interim/goethe_wortlisten_extracted.csv")
    counts = df["level"].value_counts()
    assert set(counts.index) == {"A1", "A2", "B1"}
    # B1 list is documented (CLAUDE.md) as ~2400 lexical units; headword-only
    # extraction should land in a plausible range around that, not wildly off
    assert 1500 <= counts["B1"] <= 3000
    assert counts["A1"] > 200


def test_lexical_table_schema_and_cefr_band_logic():
    df = pd.read_csv(ROOT / "data/processed/lexical_table.csv")
    required_cols = {
        "lemma", "normalized_lemma", "goethe_a1", "goethe_a2", "goethe_b1",
        "derived_cefr_band", "kde_model_count_total", "frequency_subtlex_zipf",
    }
    assert required_cols.issubset(df.columns)
    assert df["normalized_lemma"].is_unique, "one row per normalized lemma expected"
    assert set(df["derived_cefr_band"]) <= {"A1", "A2", "B1", "unclassified"}

    # conservative-assignment invariant: never A2 unless not-A1; never B1 unless not-A1/A2
    a1_rows = df[df["goethe_a1"]]
    assert (a1_rows["derived_cefr_band"] == "A1").all()
    a2_only = df[df["goethe_a2"] & ~df["goethe_a1"]]
    assert (a2_only["derived_cefr_band"] == "A2").all()
    b1_only = df[df["goethe_b1"] & ~df["goethe_a1"] & ~df["goethe_a2"]]
    assert (b1_only["derived_cefr_band"] == "B1").all()
    # never auto-assigned a band beyond B1
    assert set(df["derived_cefr_band"].unique()) <= {"A1", "A2", "B1", "unclassified"}


def test_lexical_table_never_fabricates_subtlex_frequency():
    df = pd.read_csv(ROOT / "data/processed/lexical_table.csv")
    unmatched = df[df["quality_flag_subtlex"] == "subtlex_no_direct_match"]
    assert unmatched["frequency_subtlex_zipf"].isna().all()
    assert unmatched["frequency_subtlex_raw"].isna().all()


def test_lemmatization_benchmark_sample_size_meets_minimum():
    df = pd.read_csv(ROOT / "data/interim/lemma_benchmark_sample.csv")
    assert len(df) >= 150, "CLAUDE.md requires benchmarking at least 150 stratified tokens"


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))

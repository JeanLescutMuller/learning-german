"""Phase 3: build the canonical lemma-level lexical table (first-slice version).

Joins three sources by lemma text (case-insensitive membership test for
CEFR flags; case-sensitive-then-fallback lookup for SUBTLEX-DE):

  1. KDE model-test tokens (data/interim/kde_model_test_annotated_tokens.json)
     -- gives kde_model_count_total, kde_model_count_by_section, POS.
  2. Goethe A1/A2/B1 headword lists (data/interim/goethe_wortlisten_extracted.csv)
     -- gives goethe_a1/a2/b1 boolean flags -> derived_cefr_band, per the
     CLAUDE.md rule: in A1 -> A1; not A1 but in A2 -> A2; not A1/A2 but in
     B1 -> B1; else unclassified. Never auto-assigned B2+.
  3. SUBTLEX-DE (data/raw/subtlex_de/subtlex_de_cleaned_zipf.xlsx)
     -- gives frequency_subtlex_raw/per_million/zipf. This is a SURFACE-FORM
     frequency list (190,500 word forms, not lemmas). We look up each lemma
     as-is against the "Word" column (case-sensitive first, since German
     capitalizes nouns), falling back to a capitalized-first-letter variant.
     Inflected forms that differ from the lemma (e.g. plural nouns, most
     finite verb forms) will NOT match and are flagged
     "subtlex_no_direct_match" -- CLAUDE.md explicitly forbids fabricating a
     value here, so unmatched lemmas get NaN frequency fields, not zero or
     an estimate. A full form->lemma frequency aggregation is future work
     (would require lemmatizing all 190K SUBTLEX word forms).

Output: data/processed/lexical_table.parquet and .csv.
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)


def norm(s: str) -> str:
    return s.strip().lower()


def load_goethe_flags():
    df = pd.read_csv(INTERIM / "goethe_wortlisten_extracted.csv")
    df = df[df["headword"].notna() & (df["headword"].str.len() > 1)]
    flags = {}  # norm(headword) -> {"A1":bool,"A2":bool,"B1":bool, "article":..., "forms":...}
    for _, row in df.iterrows():
        key = norm(str(row["headword"]))
        d = flags.setdefault(key, {"A1": False, "A2": False, "B1": False, "article": "", "forms": "", "headword": row["headword"]})
        d[row["level"]] = True
        if row.get("article") and not d["article"]:
            d["article"] = row["article"]
        if row.get("plural_or_forms") and not d["forms"]:
            d["forms"] = row["plural_or_forms"]
    return flags


def load_kde_tokens():
    records = json.loads((INTERIM / "kde_model_test_annotated_tokens.json").read_text(encoding="utf-8"))
    return [r for r in records if r["is_alpha"]]


def load_subtlex():
    df = pd.read_excel(RAW / "subtlex_de" / "subtlex_de_cleaned_zipf.xlsx")
    # index by exact word for O(1) lookup; keep first occurrence if dupes
    df = df.drop_duplicates(subset=["Word"], keep="first")
    return df.set_index("Word")


def subtlex_lookup(lemma: str, subtlex: pd.DataFrame):
    candidates = [lemma, lemma.capitalize(), lemma.lower()]
    for cand in candidates:
        if cand in subtlex.index:
            row = subtlex.loc[cand]
            return {
                "frequency_subtlex_raw": float(row["WFfreqcount"]),
                "frequency_subtlex_per_million": float(row["SUBTLEX"]) if "SUBTLEX" in row else None,
                "frequency_subtlex_zipf": float(row["ZipfSUBTLEX"]),
                "subtlex_match_form": cand,
                "quality_flag_subtlex": "" if cand == lemma else "matched_via_case_fallback",
            }
    return {
        "frequency_subtlex_raw": None,
        "frequency_subtlex_per_million": None,
        "frequency_subtlex_zipf": None,
        "subtlex_match_form": "",
        "quality_flag_subtlex": "subtlex_no_direct_match",
    }


def main():
    goethe = load_goethe_flags()
    kde_tokens = load_kde_tokens()
    subtlex = load_subtlex()

    # aggregate KDE lemma stats
    kde_agg = {}
    for r in kde_tokens:
        key = norm(r["lemma"])
        d = kde_agg.setdefault(
            key,
            {"lemma_surface": r["lemma"], "count_total": 0, "by_section": {}, "pos_seen": set(), "surface_forms": set()},
        )
        d["count_total"] += 1
        d["by_section"][r["section"]] = d["by_section"].get(r["section"], 0) + 1
        d["pos_seen"].add(r["pos"])
        d["surface_forms"].add(r["text"])

    all_lemmas = set(goethe.keys()) | set(kde_agg.keys())

    rows = []
    for key in sorted(all_lemmas):
        g = goethe.get(key, {"A1": False, "A2": False, "B1": False, "article": "", "forms": "", "headword": ""})
        k = kde_agg.get(key)
        lemma_display = k["lemma_surface"] if k else g["headword"]

        if g["A1"]:
            band = "A1"
        elif g["A2"]:
            band = "A2"
        elif g["B1"]:
            band = "B1"
        else:
            band = "unclassified"

        freq = subtlex_lookup(lemma_display, subtlex)

        rows.append(
            {
                "lemma": lemma_display,
                "normalized_lemma": key,
                "article_or_gender": g["article"],
                "plural_or_forms": g["forms"],
                "goethe_a1": g["A1"],
                "goethe_a2": g["A2"],
                "goethe_b1": g["B1"],
                "derived_cefr_band": band,
                "kde_model_count_total": k["count_total"] if k else 0,
                "kde_model_count_by_section": json.dumps(k["by_section"]) if k else "{}",
                "kde_pos_seen": ",".join(sorted(k["pos_seen"])) if k else "",
                "kde_surface_forms": ",".join(sorted(k["surface_forms"])) if k else "",
                **freq,
                "provenance": ";".join(
                    filter(None, [
                        "goethe_wortliste" if g["A1"] or g["A2"] or g["B1"] else "",
                        "kde_model_test" if k else "",
                        "subtlex_de" if freq["frequency_subtlex_zipf"] is not None else "",
                    ])
                ),
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(PROCESSED / "lexical_table.csv", index=False)
    df.to_parquet(PROCESSED / "lexical_table.parquet", index=False)
    print(f"Wrote {len(df)} lemma rows -> data/processed/lexical_table.{{csv,parquet}}")
    print(f"  A1={df['goethe_a1'].sum()} A2={df['goethe_a2'].sum()} B1={df['goethe_b1'].sum()} "
          f"unclassified={ (df['derived_cefr_band']=='unclassified').sum() }")
    print(f"  KDE lemmas with SUBTLEX match: {df[df['kde_model_count_total']>0]['frequency_subtlex_zipf'].notna().sum()} "
          f"/ {(df['kde_model_count_total']>0).sum()}")


if __name__ == "__main__":
    main()

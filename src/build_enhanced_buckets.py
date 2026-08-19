"""Build enhanced, mutually exclusive study buckets: A1 / A2 / B1.

Per the user's 2026-08-19 request: combine the (already-disjoint, see
build_study_lists.py) Goethe CEFR bands with the top-3,000 lemmas by
SUBTLEX-DE conversational frequency (build_frequency_lemma_rank.py),
splitting that frequency ranking across buckets as 500 / 1,000 / 1,500:

  bucket A1 = Goethe A1  UNION  frequency rank 1-500
  bucket A2 = Goethe A2  UNION  frequency rank 501-1,500   (minus anything already in A1)
  bucket B1 = Goethe B1  UNION  frequency rank 1,501-3,000 (minus anything already in A1/A2)

A word's final bucket is the EARLIEST bucket it qualifies for by either
route -- e.g. a Goethe B1 word that also happens to be extremely common
(top 500 by frequency) is promoted to bucket A1, since "top 500 most common
word" is itself a reason to learn it early regardless of its official Goethe
level. This keeps buckets disjoint (same principle as the Goethe-only
partition) and avoids ever teaching the same word twice.

Words in none of Goethe A1/A2/B1 and outside the top 3,000 SUBTLEX lemmas
are excluded entirely -- this is deliberately a *study* list, not the full
lexical table.

Caveat carried forward explicitly: "top 3,000 most commonly used words" here
means top 3,000 by SUBTLEX-DE conversational/subtitle frequency specifically
-- the only frequency source ingested so far. CLAUDE.md's fuller design
blends conversational + written + Swiss-public frequency; that blend is not
built yet, so this ranking should be read as "most common in spoken/subtitle
German," not a definitive general-frequency ranking.
"""
import re

import pandas as pd

BUCKET_ORDER = {"A1": 0, "A2": 1, "B1": 2}

# Goethe A2/B1 headword extraction is headword-only regex matching (see
# extract_goethe_pdf.py docstring) and occasionally captures a broken
# fragment: a hyphenated compound half ("Feier-"), a trailing-punctuation
# artifact ("Appetit."), a bibliography abbreviation ("Hg."), or a bare
# single letter. These carry no valid Goethe article/example and have no
# SUBTLEX frequency match either, so they cannot be corrected -- drop them
# rather than hand a learner a broken "word".
JUNK_LEMMA_RE = re.compile(r"[.,;:]$|-$|^.$|\s")


def freq_bucket(rank: float) -> str | None:
    if pd.isna(rank):
        return None
    if rank <= 500:
        return "A1"
    if rank <= 1500:
        return "A2"
    if rank <= 3000:
        return "B1"
    return None


def main() -> None:
    lex = pd.read_csv("data/processed/lexical_table.csv")
    freq = pd.read_csv("data/interim/subtlex_lemma_frequency_rank.csv")

    # collapse POS-duplicated lemma spellings, keep the dominant (highest-freq) POS
    freq = freq.sort_values("freq_sum", ascending=False)
    collapsed = (
        freq.groupby("lemma", as_index=False)
        .agg(freq_sum=("freq_sum", "sum"), pos=("pos", "first"), surface_forms=("surface_forms", "first"))
        .sort_values("freq_sum", ascending=False)
        .reset_index(drop=True)
    )
    collapsed["rank"] = collapsed.index + 1
    collapsed["lemma_key"] = collapsed["lemma"].str.lower()
    # case-variant collisions (e.g. "Sie"/"sie", "Du"/"du") can map to the same
    # lowercased key from two different rows -- keep the better (lower) rank
    # for each key, since collapsed is already sorted by freq_sum descending.
    freq_rank_by_key: dict[str, int] = {}
    freq_pos_by_key: dict[str, str] = {}
    freq_lemma_by_key: dict[str, str] = {}
    for _, r in collapsed.iterrows():
        k = r["lemma_key"]
        if k not in freq_rank_by_key:
            freq_rank_by_key[k] = r["rank"]
            freq_pos_by_key[k] = r["pos"]
            freq_lemma_by_key[k] = r["lemma"]
    top3000_keys = {k for k, rank in freq_rank_by_key.items() if rank <= 3000}

    goethe_band = dict(zip(lex["normalized_lemma"], lex["derived_cefr_band"]))
    goethe_row = lex.set_index("normalized_lemma")

    universe = top3000_keys | {
        k for k, band in goethe_band.items() if band in ("A1", "A2", "B1")
    }

    rows = []
    for key in universe:
        g_band = goethe_band.get(key, "unclassified")
        g_order = BUCKET_ORDER.get(g_band, 99)
        rank = freq_rank_by_key.get(key)
        f_band = freq_bucket(rank)
        f_order = BUCKET_ORDER.get(f_band, 99)

        final_order = min(g_order, f_order)
        final_bucket = [k for k, v in BUCKET_ORDER.items() if v == final_order][0]
        promoted = f_order < g_order  # frequency pulled it into an earlier bucket than Goethe alone would

        display_lemma = key
        article, forms = "", ""
        if key in goethe_row.index:
            row = goethe_row.loc[key]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            display_lemma = row["lemma"]
            article = row.get("article_or_gender", "") or ""
            forms = row.get("plural_or_forms", "") or ""
        elif key in freq_lemma_by_key:
            display_lemma = freq_lemma_by_key[key]

        rows.append(
            {
                "lemma": display_lemma,
                "article_or_gender": article,
                "plural_or_forms": forms,
                "pos": freq_pos_by_key.get(key, ""),
                "bucket": final_bucket,
                "goethe_band": g_band,
                "freq_rank": int(rank) if rank is not None else "",
                "promoted_by_frequency": promoted,
                "in_kde_test": bool(key in lex[lex.kde_model_count_total > 0]["normalized_lemma"].values),
            }
        )

    df = pd.DataFrame(rows).sort_values(["bucket", "freq_rank", "lemma"], na_position="last")

    n_before = len(df)
    df = df[~df["lemma"].astype(str).str.contains(JUNK_LEMMA_RE, regex=True, na=False)]
    print(f"dropped {n_before - len(df)} broken/fragment entries (hyphenated compound halves, "
          f"trailing punctuation, single letters) from Goethe extraction noise")

    for bucket in ["A1", "A2", "B1"]:
        sub = df[df.bucket == bucket]
        path = f"data/processed/enhanced_bucket_{bucket.lower()}.csv"
        sub.to_csv(path, index=False)
        n_promoted = int(sub["promoted_by_frequency"].sum())
        print(f"{bucket}: {len(sub)} words ({n_promoted} promoted early by frequency) -> {path}")

    print(f"\ntotal words across all 3 buckets: {len(df)}")
    print(f"(Goethe-only universe was 746+389+1607={746+389+1607}; "
          f"top-3000-frequency universe was {len(top3000_keys)}; union is {len(df)})")


if __name__ == "__main__":
    main()

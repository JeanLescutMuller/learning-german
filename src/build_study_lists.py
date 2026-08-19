"""Export mutually exclusive CEFR study lists from the canonical lexical table.

The Goethe A1/A2/B1 Wortlisten are cumulative, not exclusive: the B1 list
republishes A1 and A2 vocabulary too (documents everything needed at B1, not
just what's new there). derived_cefr_band in lexical_table.csv already
resolves this with the conservative rule from CLAUDE.md (in A1 -> A1; not A1
but in A2 -> A2; not A1/A2 but in B1 -> B1); this script just exports that
partition as three flat, non-overlapping study lists.
"""
import pandas as pd

COLS = ["lemma", "article_or_gender", "plural_or_forms", "kde_model_count_total", "frequency_subtlex_zipf"]


def main() -> None:
    df = pd.read_csv("data/processed/lexical_table.csv")

    bands = {
        "A1": "data/processed/study_list_a1.csv",
        "A2": "data/processed/study_list_a2_new.csv",
        "B1": "data/processed/study_list_b1_new.csv",
    }
    sizes = {}
    for band, path in bands.items():
        subset = df[df.derived_cefr_band == band].sort_values("lemma")
        subset[COLS].to_csv(path, index=False)
        sizes[band] = len(subset)
        print(f"{band}: {len(subset)} lemmas -> {path}")

    unclassified = int((df.derived_cefr_band == "unclassified").sum())
    total = sum(sizes.values()) + unclassified
    assert total == len(df), f"partition doesn't cover all rows: {total} != {len(df)}"
    print(f"unclassified (none of A1/A2/B1): {unclassified} lemmas")
    print(f"sum check: {total} == {len(df)} total lemma rows")


if __name__ == "__main__":
    main()

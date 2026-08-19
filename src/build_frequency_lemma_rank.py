"""Build a lemma-level frequency ranking from SUBTLEX-DE.

SUBTLEX-DE is a SURFACE-FORM frequency list (e.g. "ist", "sind", "war" are
separate rows) -- for a "top N words to learn" list we want LEMMA frequency
("sein" as one entry, summing all its inflected forms' counts), otherwise a
learner would see near-duplicate entries and the true rank of common verbs/
nouns would be understated.

Method: take the top TOP_N_FORMS SUBTLEX surface forms by raw frequency
(generous headroom over the ~3,000 lemmas we actually need, since many forms
collapse onto the same lemma), lemmatize each with spaCy (out of sentence
context -- single-token input, a known accuracy tradeoff vs in-context
lemmatization; see reports/lemmatization_benchmark.md for spaCy's measured
~96% in-context accuracy, which we do not re-verify here for the isolated-
token case), then sum WFfreqcount per (lemma, coarse POS) and rank.

POS is kept as part of the grouping key (not lemma alone) to avoid silently
merging homographs across word classes (e.g. "der Läufer" (NOUN, runner) vs
"laufen" (VERB, to run) share no lemma text here, but "das Licht" NOUN vs
a hypothetical "leicht"-derived form would be distinguished this way too) --
consistent with CLAUDE.md's "do not collapse homographs" requirement.
Proper nouns, punctuation, symbols and non-alphabetic tokens are dropped.
"""
import json
from pathlib import Path

import pandas as pd
import spacy

ROOT = Path(__file__).resolve().parents[1]
TOP_N_FORMS = 15000
DROP_POS = {"PROPN", "PUNCT", "SYM", "X", "SPACE"}


def main() -> None:
    subtlex = pd.read_excel(ROOT / "data/raw/subtlex_de/subtlex_de_cleaned_zipf.xlsx")
    subtlex = subtlex.sort_values("WFfreqcount", ascending=False).reset_index(drop=True)
    top_forms = subtlex.head(TOP_N_FORMS)

    nlp = spacy.load("de_core_news_sm", disable=["parser", "ner"])
    docs = nlp.pipe(top_forms["Word"].astype(str).tolist(), batch_size=1000)

    rows = []
    for word, freq, doc in zip(top_forms["Word"], top_forms["WFfreqcount"], docs):
        if len(doc) == 0:
            continue
        tok = doc[0]
        if tok.pos_ in DROP_POS or not tok.is_alpha:
            continue
        rows.append({"lemma": tok.lemma_, "pos": tok.pos_, "surface": word, "freq": int(freq)})

    tokdf = pd.DataFrame(rows)
    agg = (
        tokdf.groupby(["lemma", "pos"], as_index=False)
        .agg(freq_sum=("freq", "sum"), surface_forms=("surface", lambda s: ",".join(sorted(set(s)))))
    )
    agg = agg.sort_values("freq_sum", ascending=False).reset_index(drop=True)
    agg["rank"] = agg.index + 1

    out_path = ROOT / "data/interim/subtlex_lemma_frequency_rank.csv"
    agg.to_csv(out_path, index=False)
    print(f"{len(top_forms)} surface forms -> {len(agg)} unique (lemma,pos) pairs -> {out_path}")
    print(agg.head(20).to_string(index=False))
    print("...")
    print(f"rank 500 boundary: {agg.iloc[499]['lemma']} ({agg.iloc[499]['pos']}), freq_sum={agg.iloc[499]['freq_sum']}")
    print(f"rank 1500 boundary: {agg.iloc[1499]['lemma']} ({agg.iloc[1499]['pos']}), freq_sum={agg.iloc[1499]['freq_sum']}")
    print(f"rank 3000 boundary: {agg.iloc[2999]['lemma']} ({agg.iloc[2999]['pos']}), freq_sum={agg.iloc[2999]['freq_sum']}")


if __name__ == "__main__":
    main()

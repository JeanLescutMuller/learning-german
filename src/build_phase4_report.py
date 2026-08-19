"""Phase 4: generate the KDE lexical-difficulty coverage report.

Reads data/processed/lexical_table.csv (built by build_lexical_table.py) and
data/raw/subtlex_de/subtlex_de_cleaned_zipf.xlsx, computes the coverage
statistics CLAUDE.md's Phase 4 and "first execution milestone" ask for, and
writes reports/phase4_kde_lexical_difficulty_report.md.

Known extraction artifact filtered out here (not upstream, to keep the raw
annotated-token file honest): single-uppercase-letter tokens (A, B, C ... H)
are list-item markers from the "Anzeigen A-H" matching task (Lesen Aufgabe 3),
not vocabulary. Excluded from lemma/coverage counts, count reported separately.
"""
import re

import pandas as pd

ARTIFACT_RE = re.compile(r"^[a-zA-ZäöüÄÖÜß]$|^--$|^X$")


def main():
    lex = pd.read_csv("data/processed/lexical_table.csv")
    kde = lex[lex["kde_model_count_total"] > 0].copy()

    is_artifact = kde["lemma"].astype(str).str.match(ARTIFACT_RE)
    n_artifacts = int(is_artifact.sum())
    artifact_tokens = int(kde.loc[is_artifact, "kde_model_count_total"].sum())
    kde = kde[~is_artifact].copy()

    total_types = len(kde)
    total_tokens = int(kde["kde_model_count_total"].sum())

    band_tokens = kde.groupby("derived_cefr_band")["kde_model_count_total"].sum()
    band_types = kde.groupby("derived_cefr_band").size()

    subtlex = pd.read_excel("data/raw/subtlex_de/subtlex_de_cleaned_zipf.xlsx")
    subtlex_sorted = subtlex.sort_values("WFfreqcount", ascending=False).reset_index(drop=True)
    subtlex_sorted["rank"] = subtlex_sorted.index + 1
    rank_lookup = dict(zip(subtlex_sorted["Word"], subtlex_sorted["rank"]))
    kde["subtlex_rank"] = kde["lemma"].map(rank_lookup)
    matched = kde[kde["subtlex_rank"].notna()]

    # section/content-class breakdown (from kde_model_count_by_section JSON)
    import json as _json
    section_tokens = {}
    for _, row in kde.iterrows():
        d = _json.loads(row["kde_model_count_by_section"])
        for sec, n in d.items():
            section_tokens[sec] = section_tokens.get(sec, 0) + n

    unclassified = kde[kde["derived_cefr_band"] == "unclassified"].sort_values(
        "kde_model_count_total", ascending=False
    )
    swiss_candidates = unclassified[unclassified["frequency_subtlex_zipf"].isna()]

    lines = []
    a = lines.append
    a("# Phase 4: KDE Model-Test Lexical Difficulty Report\n")
    a("**Scope:** the single official KDE model test (`kde_modell_test.pdf`), 24 pages, "
      "annotated per the section map (`data/interim/kde_model_test_section_map.csv`). "
      f"{n_artifacts} single-letter list-marker artifacts ({artifact_tokens} token occurrences, "
      "from the \"Anzeigen A-H\" matching task labels) were excluded from all counts below.\n")
    a("**Caveat (per CLAUDE.md):** this is one model test. All figures below are point "
      "estimates from a sample of ~1,400 tokens / ~490 lemmas -- they characterize *this "
      "document*, not a statistically defended estimate of the true KDE population "
      "distribution. No confidence intervals are computed yet (would need bootstrap "
      "resampling across multiple KDE-style documents, which don't yet exist -- see "
      "Phase 7). Treat every percentage below as descriptive, not inferential.\n")

    a("## Token/lemma counts by section (Hoeren/Lesen/Schreiben content only; "
      "excludes cover, TOC, blank, and grading-stamp pages)\n")
    a("| Section | Content tokens |")
    a("|---|---|")
    for sec, n in sorted(section_tokens.items()):
        a(f"| {sec} | {n} |")
    a(f"\nTotal content tokens: **{total_tokens}**. Unique lemmas: **{total_types}**. "
      f"Lexical diversity (type/token, lemma-based): **{total_types/total_tokens:.3f}**.\n")
    a("(Hoeren's PDF content is task instructions + true/false statements only -- the actual "
      "listening source material exists solely as audio in `kde_modell_test_hoeren.mp3` and is "
      "not counted here; transcription is deferred to a later session, see source_manifest.csv.)\n")

    a("## CEFR coverage (Goethe A1/A2/B1 word lists)\n")
    a("Conservative assignment per CLAUDE.md: in A1 list -> A1; not A1 but in A2 -> A2; not "
      "A1/A2 but in B1 -> B1; otherwise unclassified (never auto-assigned B2+).\n")
    a("| Band | Lemmas (types) | % of lemmas | Token occurrences | % of tokens |")
    a("|---|---|---|---|---|")
    for band in ["A1", "A2", "B1", "unclassified"]:
        nt = int(band_types.get(band, 0))
        tk = int(band_tokens.get(band, 0))
        a(f"| {band} | {nt} | {nt/total_types:.1%} | {tk} | {tk/total_tokens:.1%} |")
    a("\n**Reading this table:** token-weighted A1 coverage (~60%) is much higher than "
      "lemma-weighted A1 coverage (~32%) because a small set of very frequent A1 function "
      "words (die/der/das, sein, sie, und, ...) account for a large share of running text, "
      "while the *unclassified* 52% of distinct lemmas -- proper nouns, Swiss/civic "
      "administrative terms, compounds -- occur mostly once each. This is exactly the "
      "'necessary vocabulary is not just the most frequent CEFR-tagged words' pattern "
      "CLAUDE.md's Phase 5 four-list design is meant to address.\n")

    a("## General-frequency coverage (SUBTLEX-DE, conversational/subtitle corpus)\n")
    a(f"Direct surface-form match against SUBTLEX-DE's 190,500-row word-form list: "
      f"**{len(matched)}/{total_types}** KDE lemmas matched "
      f"({len(matched)/total_types:.1%}). Unmatched lemmas are mostly inflected forms whose "
      "surface form differs from the lemma (plurals, conjugated verbs) -- SUBTLEX-DE is a "
      "form-frequency list, not lemma-frequency; matching all inflected forms to their lemma's "
      "aggregate frequency is deferred (would require lemmatizing the full 190K-row SUBTLEX "
      "list, out of scope for this first slice). Frequencies for unmatched lemmas are left as "
      "null, not estimated, per CLAUDE.md.\n")
    a("| Frequency band (by SUBTLEX rank) | Lemmas in band | % of matched | % of all KDE lemmas |")
    a("|---|---|---|---|")
    for cutoff in [500, 1000, 2000, 3000, 5000]:
        n = int((matched["subtlex_rank"] <= cutoff).sum())
        a(f"| top {cutoff} | {n} | {n/len(matched):.1%} | {n/total_types:.1%} |")
    beyond = total_types - int((matched["subtlex_rank"] <= 5000).sum())
    a(f"| beyond top 5000 / unranked | {beyond} | - | {beyond/total_types:.1%} |")

    a("\n## Candidate Swiss/KDE-domain vocabulary\n")
    a(f"Lemmas that are (a) not in any Goethe A1/A2/B1 list AND (b) have no SUBTLEX-DE match "
      f"at all (i.e. plausibly rare or absent in a Germany-centric subtitle corpus): "
      f"**{len(swiss_candidates)} lemmas**. This is a heuristic screen, not a confirmed Swiss-"
      "specific classification (some are simply proper nouns or compounds SUBTLEX's surface-"
      "form matching missed) -- but manual inspection of the top occurrences below confirms "
      "several genuine, high-value Swiss/civic items:\n")
    a("- **Voting/civic cluster** (KDE topic \"voting and civic information\"): Abstimmung, "
      "Stimmzettel, Stimmabgabe, Wahlbüro, Stimmrechtsausweis, Stimmbürger(in), Urne, "
      "stimmberechtigt\n")
    a("- **Swiss-specific everyday terms**: Grillade (Swiss for barbecued food), Chilbi (Swiss "
      "for funfair), Apéro, Znüni (Swiss for a mid-morning snack), Kinderhütedienst (childcare "
      "service), SPITEX (Swiss home-care organisation), gross (Swiss spelling without ß)\n")
    a("- **Municipal/administrative compounds**: Abfallsammelaktion, Schalteröffnungszeit, "
      "Notfalldienst, Hundesteuer, Gemeindesaal, Pilzkontrolle (a genuinely Swiss "
      "practice -- municipal mushroom inspection)\n")
    a("- Full ranked list: see `data/interim/kde_unclassified_lemmas.csv`\n")

    a("\n## Known extraction/annotation quality issues affecting these numbers\n")
    a("See `reports/lemmatization_benchmark.md` for the full manual benchmark "
      "(96.0% lemma accuracy / ~95% POS accuracy on 151 stratified tokens). Concretely "
      "affecting this report:\n")
    a("- `Fällanden` (place name) was lemmatized to `Fällande` and tagged NOUN instead of "
      "PROPN -- appears in the unclassified list under the wrong spelling.\n")
    a("- `Lesen` (section header \"Reading\") lemmatized to `Lese` -- an artifact of the "
      "section-header page being run through the general-content lemmatizer rather than "
      "excluded as metadata; low impact (1 occurrence).\n")
    a("- A handful of single-letter tokens from abbreviations (Fr., Sa., P., S.) were not "
      "expanded -- flagged in the benchmark as a needed manual abbreviation dictionary.\n")

    a("\n## Productive vs. receptive vocabulary (first-pass, by content class)\n")
    a("This is an *annotated judgment*, not an objective fact (per CLAUDE.md) -- content class "
      "is used here only as a structural proxy, not a semantic judgment of which specific words "
      "are truly required to answer each question:\n")
    a(f"- **Schreiben / writing_prompt** ({section_tokens.get('Schreiben', 0)} tokens): closest "
      "proxy for productive vocabulary -- words the candidate must be able to *produce*.\n")
    a(f"- **Lesen / source_text + task_apparatus, Hoeren / task_apparatus** "
      f"({section_tokens.get('Lesen', 0) + section_tokens.get('Hoeren', 0)} tokens): receptive "
      "vocabulary -- words the candidate must *recognise*, not produce.\n")
    a("A genuine productive/receptive split at the individual-word level (e.g. distinguishing "
      "which reading-passage words are load-bearing for answering vs. incidental) requires the "
      "manual/LLM question-by-question review CLAUDE.md's Phase 4 calls for and is not yet done.\n")

    with open("reports/phase4_kde_lexical_difficulty_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    unclassified[["lemma", "kde_model_count_total", "kde_pos_seen", "frequency_subtlex_zipf"]].to_csv(
        "data/interim/kde_unclassified_lemmas.csv", index=False
    )

    print("Wrote reports/phase4_kde_lexical_difficulty_report.md")
    print("Wrote data/interim/kde_unclassified_lemmas.csv")
    print(f"(excluded {n_artifacts} list-marker artifacts, {artifact_tokens} token occurrences)")


if __name__ == "__main__":
    main()

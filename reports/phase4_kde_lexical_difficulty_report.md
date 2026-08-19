# Phase 4: KDE Model-Test Lexical Difficulty Report

**Scope:** the single official KDE model test (`kde_modell_test.pdf`), 24 pages, annotated per the section map (`data/interim/kde_model_test_section_map.csv`). 13 single-letter list-marker artifacts (14 token occurrences, from the "Anzeigen A-H" matching task labels) were excluded from all counts below.

**Caveat (per CLAUDE.md):** this is one model test. All figures below are point estimates from a sample of ~1,400 tokens / ~490 lemmas -- they characterize *this document*, not a statistically defended estimate of the true KDE population distribution. No confidence intervals are computed yet (would need bootstrap resampling across multiple KDE-style documents, which don't yet exist -- see Phase 7). Treat every percentage below as descriptive, not inferential.

## Token/lemma counts by section (Hoeren/Lesen/Schreiben content only; excludes cover, TOC, blank, and grading-stamp pages)

| Section | Content tokens |
|---|---|
| Hoeren | 248 |
| Lesen | 1097 |
| Schreiben | 82 |

Total content tokens: **1427**. Unique lemmas: **476**. Lexical diversity (type/token, lemma-based): **0.334**.

(Hoeren's PDF content is task instructions + true/false statements only -- the actual listening source material exists solely as audio in `kde_modell_test_hoeren.mp3` and is not counted here; transcription is deferred to a later session, see source_manifest.csv.)

## CEFR coverage (Goethe A1/A2/B1 word lists)

Conservative assignment per CLAUDE.md: in A1 list -> A1; not A1 but in A2 -> A2; not A1/A2 but in B1 -> B1; otherwise unclassified (never auto-assigned B2+).

| Band | Lemmas (types) | % of lemmas | Token occurrences | % of tokens |
|---|---|---|---|---|
| A1 | 155 | 32.6% | 871 | 61.0% |
| A2 | 30 | 6.3% | 71 | 5.0% |
| B1 | 49 | 10.3% | 89 | 6.2% |
| unclassified | 242 | 50.8% | 396 | 27.8% |

**Reading this table:** token-weighted A1 coverage (~60%) is much higher than lemma-weighted A1 coverage (~32%) because a small set of very frequent A1 function words (die/der/das, sein, sie, und, ...) account for a large share of running text, while the *unclassified* 52% of distinct lemmas -- proper nouns, Swiss/civic administrative terms, compounds -- occur mostly once each. This is exactly the 'necessary vocabulary is not just the most frequent CEFR-tagged words' pattern CLAUDE.md's Phase 5 four-list design is meant to address.

## General-frequency coverage (SUBTLEX-DE, conversational/subtitle corpus)

Direct surface-form match against SUBTLEX-DE's 190,500-row word-form list: **365/476** KDE lemmas matched (76.7%). Unmatched lemmas are mostly inflected forms whose surface form differs from the lemma (plurals, conjugated verbs) -- SUBTLEX-DE is a form-frequency list, not lemma-frequency; matching all inflected forms to their lemma's aggregate frequency is deferred (would require lemmatizing the full 190K-row SUBTLEX list, out of scope for this first slice). Frequencies for unmatched lemmas are left as null, not estimated, per CLAUDE.md.

| Frequency band (by SUBTLEX rank) | Lemmas in band | % of matched | % of all KDE lemmas |
|---|---|---|---|
| top 500 | 97 | 26.6% | 20.4% |
| top 1000 | 143 | 39.2% | 30.0% |
| top 2000 | 181 | 49.6% | 38.0% |
| top 3000 | 201 | 55.1% | 42.2% |
| top 5000 | 236 | 64.7% | 49.6% |
| beyond top 5000 / unranked | 240 | - | 50.4% |

## Candidate Swiss/KDE-domain vocabulary

Lemmas that are (a) not in any Goethe A1/A2/B1 list AND (b) have no SUBTLEX-DE match at all (i.e. plausibly rare or absent in a Germany-centric subtitle corpus): **78 lemmas**. This is a heuristic screen, not a confirmed Swiss-specific classification (some are simply proper nouns or compounds SUBTLEX's surface-form matching missed) -- but manual inspection of the top occurrences below confirms several genuine, high-value Swiss/civic items:

- **Voting/civic cluster** (KDE topic "voting and civic information"): Abstimmung, Stimmzettel, Stimmabgabe, Wahlbüro, Stimmrechtsausweis, Stimmbürger(in), Urne, stimmberechtigt

- **Swiss-specific everyday terms**: Grillade (Swiss for barbecued food), Chilbi (Swiss for funfair), Apéro, Znüni (Swiss for a mid-morning snack), Kinderhütedienst (childcare service), SPITEX (Swiss home-care organisation), gross (Swiss spelling without ß)

- **Municipal/administrative compounds**: Abfallsammelaktion, Schalteröffnungszeit, Notfalldienst, Hundesteuer, Gemeindesaal, Pilzkontrolle (a genuinely Swiss practice -- municipal mushroom inspection)

- Full ranked list: see `data/interim/kde_unclassified_lemmas.csv`


## Known extraction/annotation quality issues affecting these numbers

See `reports/lemmatization_benchmark.md` for the full manual benchmark (96.0% lemma accuracy / ~95% POS accuracy on 151 stratified tokens). Concretely affecting this report:

- `Fällanden` (place name) was lemmatized to `Fällande` and tagged NOUN instead of PROPN -- appears in the unclassified list under the wrong spelling.

- `Lesen` (section header "Reading") lemmatized to `Lese` -- an artifact of the section-header page being run through the general-content lemmatizer rather than excluded as metadata; low impact (1 occurrence).

- A handful of single-letter tokens from abbreviations (Fr., Sa., P., S.) were not expanded -- flagged in the benchmark as a needed manual abbreviation dictionary.


## Productive vs. receptive vocabulary (first-pass, by content class)

This is an *annotated judgment*, not an objective fact (per CLAUDE.md) -- content class is used here only as a structural proxy, not a semantic judgment of which specific words are truly required to answer each question:

- **Schreiben / writing_prompt** (82 tokens): closest proxy for productive vocabulary -- words the candidate must be able to *produce*.

- **Lesen / source_text + task_apparatus, Hoeren / task_apparatus** (1345 tokens): receptive vocabulary -- words the candidate must *recognise*, not produce.

A genuine productive/receptive split at the individual-word level (e.g. distinguishing which reading-passage words are load-bearing for answering vs. incidental) requires the manual/LLM question-by-question review CLAUDE.md's Phase 4 calls for and is not yet done.

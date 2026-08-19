# KDE Vocabulary & Readiness System

Data-driven vocabulary analysis and (eventually) practice-test generation for
the **KDE (Kantonaler Deutschtest im Einbürgerungsverfahren)**, Zürich's
naturalisation German test. Built per the execution brief in `CLAUDE.md` --
read that file first for full scope, source list, and phase plan.

**Status:** first execution milestone complete (Phase 0-4 vertical slice for
the KDE model test + Goethe A1/A2/B1 lists + SUBTLEX-DE). Swiss-public corpus
(Tier 4), Swiss-German receptive mapping (Tier 5), mastery assessment,
synthetic test generator, and readiness dashboard are **not yet built** --
see "Next phases" below.

## Setup (from a clean clone)

Requires Python 3.11+ (tested with the system's Anaconda Python 3.11.7) and
internet access for the one-time data download + spaCy model.

```bash
python3 -m venv .venv
source .venv/bin/activate          # zsh/bash; use .venv\Scripts\activate on Windows
pip install -r requirements.lock
python -m spacy download de_core_news_sm
```

## Reproducing the pipeline

Run in this order. Each step reads only from `data/raw/` (immutable, already
populated) or the previous step's `data/interim/` / `data/processed/` output.

```bash
source .venv/bin/activate

# Phase 0: provenance manifest (checksums every file in data/raw/, fails
# loudly if any raw file lacks a documented source/license entry)
python src/build_manifest.py

# Phase 1: extract official KDE PDFs (layout-aware, page + word positions)
python src/extract_kde_pdf.py
python src/build_kde_section_map.py   # manually-authored page->content-class map

# Phase 2/3: extract Goethe A1/A2/B1 word lists
python src/extract_goethe_pdf.py

# Phase 3: annotate KDE model test with spaCy (tokenize/lemmatize/POS-tag)
python src/annotate_kde.py

# Phase 3: build the canonical lemma-level lexical table
# (joins KDE lemmas + Goethe CEFR flags + SUBTLEX-DE frequency)
python src/build_lexical_table.py

# Phase 4: generate the KDE lexical-difficulty coverage report
python src/build_phase4_report.py

# Export mutually exclusive CEFR study lists (A1 / A2-not-A1 / B1-not-A1-or-A2)
python src/build_study_lists.py
```

Re-downloading raw sources is not scripted yet (they were fetched once via
`curl`, by hand, with checksums recorded in `source_manifest.csv` -- see that
file for exact URLs). If you need to refresh a source, download it into the
matching `data/raw/<subdir>/` path and re-run `build_manifest.py`; it will
fail with a clear error if the new file isn't yet documented in
`src/build_manifest.py:SOURCES`.

## Repository layout

```
CLAUDE.md               execution brief (read this for full project scope)
source_manifest.csv     every raw file: URL, publisher, license, SHA-256, retrieval date
requirements.lock       exact pinned Python dependencies (pip freeze)
data/raw/                immutable downloaded sources (KDE PDFs+MP3, Goethe lists, SUBTLEX-DE)
data/interim/             extracted/annotated intermediate data (JSON/CSV)
data/processed/            canonical lexical_table.{csv,parquet}
reports/                  human-readable analysis reports
src/                        pipeline scripts, run in the order above
```

## What's in the canonical lexical table (`data/processed/lexical_table.{csv,parquet}`)

2,997 lemma rows joining:
- **Goethe A1/A2/B1 membership** (`goethe_a1/a2/b1` booleans, `derived_cefr_band`
  -- conservative: A1 > A2 > B1 > unclassified, never auto-assigned B2+)
- **KDE model-test occurrence** (`kde_model_count_total`,
  `kde_model_count_by_section`, POS tags seen, surface forms seen)
- **SUBTLEX-DE frequency** (`frequency_subtlex_raw/per_million/zipf`) --
  direct surface-form match only; unmatched inflected forms are left `null`,
  never estimated (see field `quality_flag_subtlex`)

This is **not yet** the full schema specified in `CLAUDE.md` (no Swiss-public
frequency, no compound-component breakdown, no multiword-expression handling,
no receptive/productive priority scores) -- it's the first-slice join needed
to answer the Phase 4 coverage questions.

**Important:** the Goethe A1/A2/B1 `Wortlisten` are *cumulative*, not
exclusive -- the official B1 list republishes A1 and A2 vocabulary too, so
raw `goethe_a1`/`goethe_a2`/`goethe_b1` booleans overlap heavily (e.g. 298
lemmas are flagged in all three). `derived_cefr_band` resolves this with the
conservative rule from CLAUDE.md and is what should be used for CEFR-level
analysis. Three flat, mutually exclusive study lists are exported from it by
`src/build_study_lists.py`:

- `data/processed/study_list_a1.csv` -- 746 lemmas (A1 base level)
- `data/processed/study_list_a2_new.csv` -- 389 lemmas (A2, excluding A1)
- `data/processed/study_list_b1_new.csv` -- 1,607 lemmas (B1, excluding A1 and A2)

(255 further lemmas are `unclassified` -- present in the KDE test or the raw
extraction but on none of the three Goethe lists; not exported as a separate
file since it's just `lexical_table.csv` filtered to `derived_cefr_band ==
"unclassified"`.)

## Key findings so far (see `reports/` for full detail and caveats)

- The official KDE model test: 1,427 content tokens (Hoeren+Lesen+Schreiben
  PDF text only, excluding the audio-only listening source), 476 unique lemmas.
- CEFR coverage is highly skewed by weighting: ~61% of *tokens* are A1
  vocabulary, but only ~33% of distinct *lemmas* are -- the other ~51% of
  lemma types (mostly occurring once) are proper nouns, Swiss/civic
  administrative terms, and compounds not in any Goethe list.
- Confirmed a concrete, KDE-evidenced Swiss/civic vocabulary cluster the
  general-purpose CEFR lists miss entirely: voting/civic terms (Abstimmung,
  Stimmzettel, Wahlbüro, Stimmrechtsausweis, Urne), and everyday Swiss terms
  (Grillade, Chilbi, Apéro, Znüni, SPITEX, Kinderhütedienst).
- spaCy `de_core_news_sm` lemmatization/POS benchmarked manually at 96.0%
  lemma accuracy / ~95% POS accuracy on 151 stratified KDE tokens; known
  weak spots are Swiss place names/orthography and capitalized
  sentence-initial verbs (see `reports/lemmatization_benchmark.md`).

## Next phases (not yet started)

Per `CLAUDE.md`'s phase plan: Tier 4 Swiss-public corpus (zh.ch,
stadt-zuerich.ch, ch.ch scraping), Tier 5 Swiss-German receptive mapping,
listening-audio transcription (`kde_modell_test_hoeren.mp3` is downloaded but
not yet transcribed), the four Phase-5 study-vocabulary lists with priority
scoring, personal adaptive mastery assessment, synthetic KDE-style test
generator, and the readiness dashboard.

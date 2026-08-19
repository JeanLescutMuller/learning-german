# Execution Brief for Claude: Data-Driven KDE Vocabulary and Readiness System

## Role and operating instruction

You are the implementation agent for a data-science project. Do not respond with a high-level plan and stop. Execute the work in the ordered phases below, produce the specified artifacts, test them, and report concrete results. Make reasonable technical choices where the brief leaves implementation details open. Ask questions only when a missing choice truly blocks execution.

Maintain a reproducible project: scripts, configuration, source manifest, checksums, logs, intermediate datasets, tests, and a README. Never silently invent or estimate source data. Every downloaded or extracted record must retain provenance.

## User objective

The user lives in the City of Zürich and plans to take the **KDE — Kantonaler Deutschtest im Einbürgerungsverfahren** for Swiss naturalisation.

The required KDE profile is:

- Listening and speaking: **B1**
- Reading and writing: **A2**
- Oral examination may be taken in **Standard German (Hochdeutsch)** at the candidate's request.
- At least one item in the official listening model is spoken in Swiss German, so receptive Swiss-German competence matters.

The user wants an objective, data-driven way to:

1. Measure the lexical difficulty of the official KDE model test.
2. Compare its vocabulary with general German frequency data and A1/A2/B1 vocabulary inventories.
3. Identify the vocabulary the user should actually master before attempting the KDE.
4. Separate active vocabulary required for speaking/writing from receptive vocabulary required for listening/reading.
5. Add Swiss and Zürich public-life vocabulary that generic German lists underrepresent.
6. Generate many synthetic KDE-style practice tests at calibrated difficulty levels.
7. Track performance and decide, with a safety margin, when the user is ready.

This is not a project to rank literally every possible German word. German productively forms compounds, making that goal ill-defined. The operational unit must be a **lexical entry centered on a lemma**, retaining surface forms, senses when necessary, multiword expressions, separable verbs, and compound components.

## Official KDE context and primary references

Treat official Zürich and SEM sources as authoritative for the examination. Do not infer exam rules from blogs when an official rule exists.

### Official KDE materials

- KDE information page, model-test downloads and approved providers:  
  <https://www.zh.ch/de/migration-integration/einbuergerung/kantonaler-deutschtest.html>
- Official 24-page written model test:  
  <https://www.zh.ch/content/dam/zhweb/bilder-dokumente/themen/migration-integration/einbuerung/kde/kde_modell_test.pdf>
- Official answer key:  
  <https://www.zh.ch/content/dam/zhweb/bilder-dokumente/themen/migration-integration/einbuerung/kde/kde_modell_test_loesungsschluessel.pdf>
- Official KDE administration regulations, including the oral format and language choice:  
  <https://www.zh.ch/content/dam/zhweb/bilder-dokumente/themen/migration-integration/einbuerung/kde/reglement_gemeinden_testanbieter_kde_okt_2021.pdf>
- City of Zürich language-requirement page:  
  <https://www.stadt-zuerich.ch/de/lebenslagen/einwohner-services/einbuerung/deutschkenntnisse.html>
- Current SEM list of recognised certificates, edition 1 July 2026:  
  <https://www.sem.admin.ch/dam/sem/de/data/integration/themen/sprache/anerkannte-sprachzertifikate.pdf.download.pdf/anerkannte-sprachzertifikate-d.pdf>

### Official test structure to encode

From the official regulations and model test:

- Written test:
  - Listening: four tasks, approximately 15 minutes
  - Reading: four tasks, approximately 35 minutes
  - Writing: one task, approximately 25 minutes
- Oral test: approximately 15–20 minutes
  - Task 1: introduce oneself for approximately two minutes using prompts such as name, residence, family, work and leisure.
  - Task 2: select a scenario picture and speak about the everyday topic for approximately five minutes, with examiner follow-up questions.
- Written and oral components are assessed separately.
- The published regulations state a 60% pass threshold for each component.
- Candidates choose Standard German or Swiss German for the oral interaction; examiners follow that choice.

Do not conflate exam instructions, source passages and answer options. Analyse each separately.

## Source hierarchy for vocabulary data

Use a multi-source model. No single source should become “the true ranking.” Preserve each source-specific score and derive a composite only after inspecting coverage and biases.

### Tier 1: pedagogical CEFR/exam inventories

1. **Goethe-Zertifikat A1 vocabulary list**  
   <https://www.goethe.de/pro/relaunch/prf/de/A1_SD1_Wortliste_02.pdf>
2. **Goethe-Zertifikat A2 vocabulary list**  
   <https://www.goethe.de/pro/relaunch/prf/de/Goethe-Zertifikat_A2_Wortliste.pdf>
3. **Goethe/ÖSD/University of Fribourg B1 vocabulary list**  
   <https://www.goethe.de/pro/relaunch/prf/de/Goethe-Zertifikat_B1_Wortliste.pdf>

The B1 source states that it contains approximately 2,400 lexical units intended for at least receptive mastery and follows a pluricentric approach that includes Swiss Standard German variants such as *parkieren*. These are examination inventories, not universal CEFR definitions. The CEFR itself specifies capabilities, not an official universal word-to-level mapping.

Derive a conservative pedagogical level:

- In A1 list → A1
- Not A1 but in A2 list → A2
- Not A1/A2 but in B1 list → B1
- Otherwise → unclassified, never automatically B2+

Preserve phrases and examples only as allowed by licensing. Do not redistribute copyrighted source lists wholesale in a public artifact. Store source metadata and derived membership flags; confirm permitted use before publishing extracted content.

### Tier 2: spoken/conversational frequency

Use **SUBTLEX-DE**, a German subtitle-frequency resource, as a conversational proxy. Start from the project/paper and follow the authoritative data link:

- Brysbaert et al., SUBTLEX-DE paper/data landing material:  
  <https://osf.io/download/ayh2q>

Verify the actual dataset version, fields, terms of use and checksum. Subtitle frequency is valuable for everyday listening but is not a Swiss corpus and is biased by entertainment dialogue.

### Tier 3: written/general German frequency

Use at least one corpus-based written list:

1. **Leipzig Corpora Collection / Wortschatz Leipzig**  
   <https://wortschatz.uni-leipzig.de/en>  
   Frequency-dictionary description: <https://wortschatz-leipzig.de/en/freqdict>
2. **DeReWo — IDS Mannheim corpus-based lemma and word-form lists**  
   <https://www.ids-mannheim.de/en/s/corpus-linguistics/projects/methods-of-analysis/corpus-based-lemma-and-word-form-lists/>

If both are practically downloadable and their licenses permit this use, ingest both. Otherwise ingest the best licensed source and document why the other was excluded. News/web frequency is useful for KDE reading but will overrepresent politics, named entities and current events.

### Tier 4: Swiss Standard German and public-life corpus

Create a focused, reproducible corpus of public pages/documents from authoritative Swiss sources. Respect robots.txt, copyright and rate limits. Store URLs and retrieval dates, not merely copied text.

Priority domains and topics:

- `zh.ch`: naturalisation, municipalities, waste/recycling, schools, health, voting, permits, events
- `stadt-zuerich.ch`: municipal services, emergency information, public facilities, neighbourhood life
- `ch.ch`: federal everyday administrative information
- Public transport information from official Zürich/Swiss operators where permitted
- Public-health and emergency guidance from official Swiss sources

Create topic labels aligned with plausible KDE situations:

- authorities and registration
- work and workplace
- housing and neighbours
- health, doctor and pharmacy
- transport and directions
- school and childcare
- shopping and services
- waste and recycling
- appointments, invitations and events
- leisure and sport
- emergencies
- voting and civic information
- telephone messages and opening hours

This corpus corrects the Germany-centric bias of general corpora. Do not let it dominate common function words merely because pages reuse navigation or legal boilerplate. Strip menus, cookie notices, headers, footers and duplicated templates.

### Tier 5: Swiss-German receptive layer

Maintain a separate mapping for high-value Swiss-German listening forms. Do not merge dialect spellings directly into Standard German counts. Map dialect surface forms to Standard German lemmas and tag them as receptive-only unless the user chooses otherwise.

Seed examples include *nöd → nicht*, *öppis → etwas*, *hüt → heute*, *gaa → gehen*, and *zruggrüefe → zurückrufen*. Verify forms with reputable Swiss sources before inclusion. Add items encountered in the official audio and permitted Swiss conversational data.

## Required data model

Produce a canonical lexical table, preferably Parquet plus CSV export, with fields equivalent to:

```text
lexeme_id
lemma
normalized_lemma
part_of_speech
sense_id_optional
surface_forms
separable_verb_parts
multiword_expression
compound_components
article_or_gender
plural_form
frequency_subtlex_raw
frequency_subtlex_per_million
frequency_subtlex_zipf
frequency_written_raw_by_source
frequency_written_per_million_by_source
frequency_written_zipf_by_source
document_frequency_by_source
frequency_swiss_public
document_frequency_swiss_public
goethe_a1
goethe_a2
goethe_b1
derived_cefr_band
swiss_standard_variant
swiss_german_forms
kde_model_count_total
kde_model_count_by_section
kde_model_document_frequency
kde_topic_tags
receptive_priority
productive_priority
provenance
license
quality_flags
```

Store counts and normalized scores. Do not retain only ranks: tied and cross-corpus ranks are hard to interpret.

## NLP normalization requirements

Implement and evaluate, not merely mention:

1. Unicode normalization, preserving `ä`, `ö`, `ü`, `ß` and Swiss `ss` variants.
2. Sentence segmentation and tokenisation.
3. Lemmatization and part-of-speech tagging.
4. Separable-verb reconstruction where feasible.
5. Named-entity, number, date, time, URL and abbreviation handling.
6. Compound splitting with confidence scores.
7. Multiword-expression preservation for exam-useful chunks.
8. Manual override dictionaries for KDE and Swiss public vocabulary.

Use a modern German NLP model such as spaCy or Stanza, but benchmark it manually on at least 150 stratified tokens from the KDE material. Report lemma accuracy, POS accuracy and compound-split error patterns. Preserve both raw and corrected annotations.

Examples requiring care:

- *geht, ging, gegangen* → *gehen*
- *Kollegen, Kolleginnen* → gender-aware lexeme relation, not naïve deletion
- *meldet sich an* → *sich anmelden*
- *Stimmrechtsausweis* → *Stimmrecht + Ausweis*, with deeper components optional
- *Kinderhütedienst* → Swiss/public-life term whose components may be common even when the compound is rare

## Phase-by-phase execution

### Phase 0 — repository and provenance

Create:

```text
README.md
pyproject.toml or requirements.lock
config/
data/raw/
data/interim/
data/processed/
reports/
src/
tests/
source_manifest.csv
```

The manifest must contain URL, publisher, title, version/date, retrieval timestamp, checksum, license/terms, intended use and processing script.

### Phase 1 — acquire and validate official materials

Download the KDE PDFs, answer key, regulations and listening MP3 from the official page. Verify MIME types, file sizes and checksums. Extract PDF text with layout information. Transcribe the official audio locally if lawful and technically possible, then manually flag uncertainty—especially the Swiss-German segment. Do not claim an automatic dialect transcription is authoritative.

Create a section map distinguishing:

- instructions
- listening transcript
- reading source text
- writing prompt
- questions
- answer options
- answer key

### Phase 2 — acquire vocabulary and corpus sources

Download the licensed datasets. Record exclusions and access failures. Never substitute an unverified GitHub mirror without provenance when an authoritative version is available.

### Phase 3 — normalize and integrate

Normalize each source independently, then join through lemma + POS, with explicit many-to-many handling. Do not collapse homographs such as noun/verb uses into one opaque record. Preserve source scores rather than averaging immediately.

Compute Zipf frequency when token totals are known:

```text
zipf = log10(frequency_per_billion)
```

If corpus totals are unavailable, do not fabricate Zipf values. Retain rank/relative frequency with a quality flag.

### Phase 4 — annotate and analyse the KDE model

Report separately for each section and content class:

- token count
- unique surface forms
- unique lemmas
- lexical diversity
- A1/A2/B1/unclassified token and type coverage
- top-500/1,000/2,000/3,000/5,000 frequency coverage
- spoken-frequency and written-frequency percentiles
- Swiss Standard German items
- Swiss-German receptive items
- compounds and component transparency
- proper nouns, dates and numbers
- words necessary versus unnecessary for answering each question

The final distinction requires careful human/LLM review. Mark it as annotated judgment, not objective fact.

Bootstrap passages or tasks to display uncertainty. One model test is too small to estimate the true KDE distribution precisely. Do not present single-point estimates without confidence intervals or sensitivity analysis.

### Phase 5 — derive the study vocabulary

Create **four lists**, not one:

1. **Core productive vocabulary**: words and chunks the user should actively produce in oral answers and short writing.
2. **Core receptive vocabulary**: words that must be recognised quickly in reading and Standard German listening.
3. **Swiss/KDE domain vocabulary**: administrative, civic and everyday Swiss terms underrepresented in general lists.
4. **Swiss-German listening recognition**: dialect-to-standard mappings, not production targets.

Assign priority using an interpretable model. Begin with separate standardized features and then test weights:

```text
priority =
    encounter_probability
  * comprehension_or_production_value
  * kde_topic_relevance
  * (1 - personal_mastery_probability)
  / estimated_learning_cost
```

Encounter probability must combine, without hiding components:

- conversational frequency
- written frequency
- Swiss-public frequency
- CEFR membership
- KDE-model occurrence
- coverage across KDE topics/documents

Avoid overfitting to the sole model test. Cap or shrink the KDE-sample boost. Use sensitivity analyses over plausible weights and report which words remain high-priority across specifications.

### Phase 6 — personal mastery measurement

Design an assessment that estimates, independently:

- receptive recognition
- meaning recall
- listening recognition
- productive recall
- correct use in a sentence
- Swiss-German recognition

Use adaptive sampling across frequency/CEFR/topic strata. Do not ask the user to test all 2,400 entries individually before producing value. Start with a statistically useful sample, infer uncertain bands, and actively sample near the mastery boundary.

Store mastery as probabilities with timestamps and evidence counts, not a binary known/unknown flag. Support spaced repetition export, ideally Anki-compatible TSV/CSV, while retaining example context and source provenance.

### Phase 7 — synthetic KDE-style test generator

Build templates for the official task families rather than generating unconstrained prose.

Each generated test must specify:

- task family
- topic
- target length
- target CEFR distribution
- target frequency-band distribution
- Swiss-domain vocabulary quota
- grammar constraints
- number and type of questions
- answer key and textual evidence
- difficulty band relative to the official sample

Produce at least five bands:

- KDE −20%
- KDE −10%
- KDE-equivalent
- KDE +10%
- KDE +20%

These labels must be defined by measured features, not intuition. Because the source test is small, call them “model-relative difficulty bands,” not verified real-exam difficulty.

Validation pipeline for every generated item:

1. Generate passage and questions.
2. Independently solve them without seeing the proposed answer key.
3. Reject ambiguous or unsupported questions.
4. Verify each correct answer against an exact evidence span.
5. Check distractors for uniqueness and plausibility.
6. Measure lexical and syntactic statistics.
7. Reject passages outside configured tolerances.
8. Deduplicate against prior generated tests and official material.

Never reproduce or lightly paraphrase copyrighted official questions at scale. Generate new topics, entities, times, prices and situations while preserving task mechanics.

For listening practice, create Standard German audio and a limited, clearly labelled Swiss-German receptive subset. Do not use an unreliable generic TTS voice and label it authentic Zürich dialect. Record dialect source/voice provenance.

### Phase 8 — readiness score

Do not reduce readiness to vocabulary alone. Construct a dashboard with:

- unseen-test reading accuracy and time
- unseen-test listening accuracy and time
- writing task completion, intelligibility and required-point coverage
- oral duration, comprehensibility, interaction and follow-up response
- receptive lexical coverage
- productive lexical/chunk mastery
- Swiss-German listening recognition
- performance stability across topics and dates

Suggested conservative readiness rule, to be calibrated rather than blindly adopted:

- At least five unseen, full, model-relative KDE-equivalent tests passed under time limits.
- At least three unseen KDE +10% tests passed.
- No critical section below the official threshold in recent attempts.
- Use a safety target materially above 60%, such as 75–80%, subject to calibration.
- Demonstrate performance across multiple topic families.
- Complete at least three independently assessed oral simulations and three writing tasks.

Report uncertainty and weakest skill. A single aggregate score must never hide a failing component.

## Difficulty model

Maintain separate dimensions:

### Lexical difficulty

- spoken and written log frequency
- CEFR membership
- word length and syllable count
- morphological complexity
- compound transparency
- polysemy
- cognate status for a French-native, English-fluent learner
- Swiss specificity
- contextual predictability

### Syntactic difficulty

- sentence length
- dependency length/depth
- subordinate clauses
- verb-final structures
- separable verbs
- passive voice
- nominalisations
- pronoun/reference resolution

### Task difficulty

- number of facts
- need for inference versus direct matching
- distractor similarity
- audio speed/noise/accent
- whether audio is played once
- time pressure
- required productive length

Never describe a text as “A2” solely because most words appear in an A2 list.

## Initial weighting policy

Do not prematurely merge all frequencies into one opaque rank. First publish a multi-axis view. For an optional composite general-frequency score, begin with a documented, adjustable baseline such as:

```text
35% conversational/subtitle frequency
30% general written frequency
25% Swiss-public frequency
10% cross-source document dispersion
```

Then calculate a separate KDE relevance adjustment. These are starting hypotheses, not truths. Run sensitivity analysis with materially different weights and retain stable-priority words.

For productive vocabulary, increase conversational frequency, reusable verbs, connectors and chunks. For receptive reading vocabulary, increase written and Swiss-public frequency. Do not use the same ranking for all four skills.

## Expected deliverables

At minimum, produce:

1. Reproducible source manifest with licensing notes.
2. Canonical lemma-level lexical database in Parquet.
3. Human-readable CSV exports for the four study lists.
4. KDE model-test annotated corpus.
5. KDE lexical-difficulty report with charts and uncertainty.
6. Coverage table by frequency bands and CEFR bands.
7. Swiss/KDE vocabulary supplement.
8. Swiss-German receptive mapping.
9. Personal adaptive vocabulary assessment.
10. Synthetic practice-test generator with validation tests.
11. An initial set of at least 10 validated written practice tasks distributed across difficulty bands.
12. Oral prompt generator and scoring rubric.
13. Readiness dashboard or report.
14. README with exact commands from a clean environment.
15. Unit and integration tests.

## Quality gates

Do not proceed silently past a failed gate.

- All external sources have provenance and an explicit license/terms note.
- Raw source files are immutable.
- KDE extraction is manually spot-checked against the PDF/audio.
- Lemmatization benchmark is reported.
- Duplicates and homographs are handled explicitly.
- Frequency normalization never assumes an unknown corpus size.
- CEFR labels are represented as source membership, not universal truth.
- Swiss-public corpus boilerplate is removed and deduplicated.
- Synthetic questions have independently verified answers.
- Generated difficulty is measured and falls within tolerance.
- Readiness is evaluated separately by skill.

## First execution milestone

Begin immediately with a minimal but complete vertical slice:

1. Create the repository structure and source manifest.
2. Acquire official KDE materials and the three Goethe lists, subject to terms.
3. Extract and manually validate the KDE written model test.
4. Build the initial lemma table using the Goethe lists plus one licensed frequency source.
5. Produce a first report answering:
   - What proportion of KDE tokens and lemmas belong to A1, A2 and B1 inventories?
   - What proportion lies in each general-frequency band?
   - Which unclassified or rare items are Swiss/KDE relevant?
   - Which words/chunks appear to need productive versus receptive mastery?
   - How sensitive are conclusions to lemmatization and compound splitting?
6. Present the concrete outputs and limitations, then continue to the Swiss corpus and synthetic generator unless a genuine blocker exists.

Do not end the first response with only a proposed plan. Start executing and return file paths, commands run, dataset counts, validation results and the next active phase.

## Communication style

Be concise and empirical. Distinguish:

- verified facts
- implementation choices
- assumptions
- inferred annotations
- unresolved uncertainty

When blocked by access or licensing, state the exact source, error and safe alternative. Never fill missing data with invented values.

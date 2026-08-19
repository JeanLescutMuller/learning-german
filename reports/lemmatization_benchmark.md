# spaCy `de_core_news_sm` Lemmatization/POS Benchmark on KDE Model Test

**Method:** 151 alpha tokens (target: at least 150, per CLAUDE.md) sampled with
proportional stratification across (section, content_class) groups from the
full annotated KDE model-test token set (`data/interim/kde_model_test_annotated_tokens.json`,
1729 tokens total). Each sampled (surface form, lemma, POS) triple was manually
checked by re-reading the token in its original sentence context in the source
PDF text (`data/interim/kde_modell_test_extracted.json`). Sample:
`data/interim/lemma_benchmark_sample.csv` (see also scratchpad copy used during
review). This is a judgment annotation (LLM-assisted manual review), not an
automated ground truth.

## Headline results

| Metric | Correct | Total | Accuracy |
|---|---|---|---|
| Lemma accuracy | 145 | 151 | **96.0%** |
| POS accuracy | 144-145 | 151 | **~95.4-96.0%** |
| Either wrong (token-level) | 141 correct | 151 | **93.4%** |

(POS accuracy has a one-token judgment call -- see "Falsch" below -- hence the range.)

## Errors found, by pattern

1. **Swiss place names / dialect spellings mis-lemmatized as if weak nouns.**
   - `Fällanden` (a village name) -> lemma `Fällande`, POS `NOUN` (should stay
     `Fällanden`, POS `PROPN`). Occurred twice in sample.
   - `Warenmärt` (Swiss-dialect spelling of `Warenmarkt`, "goods market") -> POS
     `PROPN` (should be `NOUN`; lemma was at least left unmodified, which is
     the safer failure mode).
   - Pattern: the small German model has weak coverage of Swiss toponyms and
     Swiss-orthography variants -- directly relevant to this project's Tier 4/5
     Swiss-specific vocabulary work, and a concrete argument for the manual
     override dictionary CLAUDE.md calls for.

2. **Capitalized sentence-initial imperative verbs misread as nominalizations.**
   - `Rufen` (from "**Rufen** Sie in Notfällen immer zuerst Ihren Hausarzt an")
     -> lemma `Rufe`, POS `NOUN` (should be `rufen`, `VERB`). German capitalizes
     both sentence-initial words and all nouns, so a capitalized verb at a
     sentence boundary is genuinely ambiguous without deeper context -- this is
     the general-purpose small model's known failure mode.
   - `Lesen` (section header "Lesen" = the infinitival-noun heading "Reading")
     -> lemma `Lese`, POS `NOUN`; arguably closer to correct (infinitival
     nouns are legitimate), but "Lese" strips the wrong suffix. Flagged.

3. **Comparative adjective under-lemmatized.**
   - `weiteren` (from "weitere Attraktionen", comparative-derived "further/
     additional") -> lemma `weit` (base positive "far/wide") instead of
     `weiter` (the comparative lexeme actually in use). Confirms CLAUDE.md's
     concern about naive stemming losing morphological distinctions that
     matter for meaning.

4. **Common noun over-tagged as proper noun.**
   - `Papierabfuhr` ("paper collection", a compound common noun) -> POS
     `PROPN`. Likely a capitalization-based heuristic misfiring on a bolded ad
     heading.

5. **Answer-apparatus labels (Ja/Nein/Richtig/Falsch) get generic content POS.**
   - `Nein` -> POS `NOUN` (arguably `INTJ` or a discourse particle).
   - `Falsch` -> POS `ADV` (arguably `ADJ`, its canonical citation form).
   - Low practical impact: these are checkbox-column headers, not exam
     content vocabulary, and are already isolated in the `task_apparatus`
     content class rather than `source_text`.

6. **Abbreviations left unexpanded (confirms CLAUDE.md Phase-3 requirement).**
   - `Sa` (= Samstag, "Saturday") and `Fr` (= Franken, the currency, in a
     price listing "Fr. 140.--") both pass through as their own lemma with
     POS `NOUN`/`PROPN`. No abbreviation-expansion dictionary is applied yet;
     this is exactly the gap CLAUDE.md's NLP-normalization requirement #5
     anticipates ("Named-entity, number, date, time, URL and abbreviation
     handling").

## What worked well (worth noting, not just failures)

- Strong-verb and separable-verb lemmatization was accurate in every sampled
  case: `verletzt`->`verletzen`, `sucht`->`suchen`, `zurückrufen`->
  `zurückrufen`, `ausfüllen`->`ausfüllen`, `gebündelt`->`bündeln`,
  `erhalten`->`erhalten`, `anmelden`->`anmelden`.
- Long transparent compounds were split/lemmatized correctly as single nouns
  without fragmentation: `Abfallsammelaktion`, `Kunstausstellung`,
  `Papierabfuhr` (lemma correct even though POS was wrong), `Stimmabgabe`,
  `Telefonbeantworter`.
- Swiss Standard German orthography (`gross` not `groß`) was preserved
  as-is, not "corrected" to German-German spelling -- important for this
  project's Swiss-variant handling.
- A genuinely Swiss-specific lexical item, `Grilladen` (Swiss for "grilled
  food" / barbecue), was lemmatized correctly and consistently (`Grillade`)
  across both occurrences in the sample -- worth flagging as a Tier
  4/5 Swiss-vocabulary candidate since it will not appear in Germany-centric
  frequency corpora.
- Gendered noun forms were preserved as distinct lemmas rather than naively
  collapsed (`Kolleginnen` -> `Kollegin`, not merged into `Kollege`) --
  consistent with CLAUDE.md's requirement to treat gender pairs as a relation,
  not deletion (a full gender-pair *relation* table is still a later-phase
  task; today's result only confirms the lemmatizer doesn't destroy the
  distinction).

## Implication for downstream phases

- Lemma/POS accuracy in the mid-90s is usable for the coverage statistics in
  Phase 4 (aggregate counts tolerate a handful of point errors), but is **not**
  sufficient on its own for the canonical lexical database without: (a) a
  manual override dictionary for Swiss toponyms/orthography and known KDE
  proper nouns (Fällanden, Greifensee, Warenmärt, Stadtspital, etc.), and
  (b) an abbreviation-expansion table (Sa/So/Mo.../Fr./Rp./usw.). Both are
  explicit CLAUDE.md deliverables for a later phase, not yet built.
- Compound splitting was not exercised much by this sample (most compounds
  stayed intact as single lemmas, which is actually the *desired* behavior
  per CLAUDE.md's "compound components... optional" -- deep splitting is a
  separate, lower-priority feature for later phases).

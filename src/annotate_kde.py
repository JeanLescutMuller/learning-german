"""Annotate the KDE model test with spaCy: tokenize, lemmatize, POS-tag.

Uses a simplified page-level content-class mapping derived from
data/interim/kde_model_test_section_map.csv. The section map itself
distinguishes instructions/questions/answer_options at a finer grain than
is practical to auto-extract without additional bounding-box markup (see
that file's docstring), but for the Hoeren task pages and the Lesen
question pages, those three sub-classes always share one page with no
separate source_text -- so this script pools them per page into one of:

  task_apparatus  - instructions + questions + answer_options (Hoeren
                     pages 6-9; Lesen question pages 12/14/16/18)
  source_text     - the Lesen reading passages, each on its own page
                     (13/15/17/19); Hoeren has NO source_text in the PDF
                     (spoken only -- excluded here, flagged separately)
  writing_prompt  - the Schreiben task prompt (page 22)
  excluded        - metadata, section headers, blank pages, the blank
                     response_area (page 23) -- not exam vocabulary

The "© Gemeindeamt des Kantons Zuerich KDE_Modell-Test Seite N/24" footer
is stripped from every page (boilerplate, not exam content).
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import spacy

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"

PAGE_CLASS = {
    6: ("Hoeren", "task_apparatus"), 7: ("Hoeren", "task_apparatus"),
    8: ("Hoeren", "task_apparatus"), 9: ("Hoeren", "task_apparatus"),
    12: ("Lesen", "task_apparatus"), 13: ("Lesen", "source_text"),
    14: ("Lesen", "task_apparatus"), 15: ("Lesen", "source_text"),
    16: ("Lesen", "task_apparatus"), 17: ("Lesen", "source_text"),
    18: ("Lesen", "task_apparatus"), 19: ("Lesen", "source_text"),
    22: ("Schreiben", "writing_prompt"),
}

FOOTER_RE = re.compile(r"©\s*Gemeindeamt des Kantons Z[üu]rich.*?Seite \d+/24")


def load_pages():
    data = json.loads((INTERIM / "kde_modell_test_extracted.json").read_text(encoding="utf-8"))
    return {p["page_number"]: FOOTER_RE.sub("", p["text"]).strip() for p in data}


def main():
    nlp = spacy.load("de_core_news_sm")
    pages = load_pages()

    records = []  # one per (page, section, class, token)
    for page_num, (section, cls) in PAGE_CLASS.items():
        text = pages.get(page_num, "")
        doc = nlp(text)
        for tok in doc:
            if tok.is_space or tok.is_punct:
                continue
            records.append(
                {
                    "page": page_num,
                    "section": section,
                    "content_class": cls,
                    "text": tok.text,
                    "lemma": tok.lemma_,
                    "pos": tok.pos_,
                    "is_alpha": tok.is_alpha,
                    "like_num": tok.like_num,
                }
            )

    out = INTERIM / "kde_model_test_annotated_tokens.json"
    out.write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {len(records)} annotated tokens -> {out}")

    # Quick per-(section, content_class) summary
    by_group = defaultdict(list)
    for r in records:
        by_group[(r["section"], r["content_class"])].append(r)

    print(f"\n{'section':<12}{'class':<16}{'tokens':>8}{'types':>8}{'lemmas':>8}")
    for (section, cls), recs in sorted(by_group.items()):
        alpha = [r for r in recs if r["is_alpha"]]
        types = len(set(r["text"].lower() for r in alpha))
        lemmas = len(set(r["lemma"].lower() for r in alpha))
        print(f"{section:<12}{cls:<16}{len(alpha):>8}{types:>8}{lemmas:>8}")


if __name__ == "__main__":
    main()

"""Build the KDE model-test section map: page -> content class.

Manually authored from reading data/interim/kde_modell_test_extracted.json
and kde_modell_test_loesungsschluessel_extracted.json in full (see
scratchpad review, 2026-08-19). This is a human/LLM judgment annotation,
not an automatic extraction -- CLAUDE.md requires instructions, source
passages, questions and answer options to be distinguished explicitly
rather than conflated.

content_class values:
  metadata         - cover, TOC, blank pages, grading stamp page
  section_header    - "Hören / 4 Aufgaben / 15 Minuten" style header page
  instructions      - task-level instructions ("Sie hören ein Gespräch...")
  questions         - the numbered items/statements being judged or answered
  answer_options    - multiple-choice options or richtig/falsch/ja-nein checkboxes
  source_text       - the reading passage / listening-audio-only content
  writing_prompt    - the Schreiben task prompt and bullet points
  response_area     - blank lines for candidate's own writing (no exam content)
  answer_key        - correct answers from the Loesungsschluessel document

Audio: the Hoeren section's actual source content (the spoken dialogues/
announcements) exists only in kde_modell_test_hoeren.mp3, not in the PDF.
The PDF only contains task instructions + the statements to judge. This is
marked explicitly (source_text = "AUDIO ONLY - see mp3, transcription deferred").
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "kde_model_test_section_map.csv"

ROWS = [
    # doc, page, section (Hören/Lesen/Schreiben/front/back), aufgabe, content_class, description
    ("model_test", 1, "front", None, "metadata", "Cover page: candidate name/DOB fields"),
    ("model_test", 2, "front", None, "metadata", "Blank (page footer only)"),
    ("model_test", 3, "front", None, "metadata", "Table of contents"),
    ("model_test", 4, "front", None, "metadata", "Blank (page footer only)"),
    ("model_test", 5, "Hoeren", None, "section_header", "'Hören / 4 Aufgaben / 15 Minuten'"),
    ("model_test", 6, "Hoeren", 1, "instructions", "Task framing: street conversation, read statements first"),
    ("model_test", 6, "Hoeren", 1, "questions", "4 richtig/falsch statements about the conversation"),
    ("model_test", 6, "Hoeren", 1, "answer_options", "Richtig/Falsch checkboxes"),
    ("model_test", 6, "Hoeren", 1, "source_text", "AUDIO ONLY - see kde_modell_test_hoeren.mp3, transcription deferred"),
    ("model_test", 7, "Hoeren", 2, "instructions", "Task framing: answering-machine message, read statements first"),
    ("model_test", 7, "Hoeren", 2, "questions", "3 richtig/falsch statements"),
    ("model_test", 7, "Hoeren", 2, "answer_options", "Richtig/Falsch checkboxes"),
    ("model_test", 7, "Hoeren", 2, "source_text", "AUDIO ONLY - see kde_modell_test_hoeren.mp3, transcription deferred"),
    ("model_test", 8, "Hoeren", 3, "instructions", "Task framing: radio announcement, read statements first"),
    ("model_test", 8, "Hoeren", 3, "questions", "3 richtig/falsch statements"),
    ("model_test", 8, "Hoeren", 3, "answer_options", "Richtig/Falsch checkboxes"),
    ("model_test", 8, "Hoeren", 3, "source_text", "AUDIO ONLY - see kde_modell_test_hoeren.mp3, transcription deferred"),
    ("model_test", 9, "Hoeren", 4, "instructions", "Task framing: answering-machine message; explicitly flagged as Swiss German ('auf Schweizerdeutsch gesprochen')"),
    ("model_test", 9, "Hoeren", 4, "questions", "3 richtig/falsch statements"),
    ("model_test", 9, "Hoeren", 4, "answer_options", "Richtig/Falsch checkboxes"),
    ("model_test", 9, "Hoeren", 4, "source_text", "AUDIO ONLY, SWISS GERMAN - see kde_modell_test_hoeren.mp3, transcription deferred, flag uncertainty"),
    ("model_test", 10, "Hoeren", None, "metadata", "Blank (page footer only)"),
    ("model_test", 11, "Lesen", None, "section_header", "'Lesen / 4 Aufgaben / 35 Minuten'"),
    ("model_test", 12, "Lesen", 1, "instructions", "Task framing: Sommerfest Fällanden, single correct answer per question"),
    ("model_test", 12, "Lesen", 1, "questions", "7 questions about the event programme"),
    ("model_test", 12, "Lesen", 1, "answer_options", "3 multiple-choice options per question"),
    ("model_test", 13, "Lesen", 1, "source_text", "Full event programme text (Sommerfest Fällanden)"),
    ("model_test", 14, "Lesen", 2, "instructions", "Task framing: Tag der offenen Tür Stadtspital"),
    ("model_test", 14, "Lesen", 2, "questions", "6 questions about the open-house announcement"),
    ("model_test", 14, "Lesen", 2, "answer_options", "3 multiple-choice options per question"),
    ("model_test", 15, "Lesen", 2, "source_text", "Full announcement text (Stadtspital open house)"),
    ("model_test", 16, "Lesen", 3, "instructions", "Task framing: match 5 situations to 8 ads (3 ads unused)"),
    ("model_test", 16, "Lesen", 3, "questions", "5 situations to match"),
    ("model_test", 16, "Lesen", 3, "answer_options", "8 short ads A-H are the answer options (matching task)"),
    ("model_test", 17, "Lesen", 3, "source_text", "8 short classified-ad style texts A-H (also functions as answer_options)"),
    ("model_test", 18, "Lesen", 4, "instructions", "Task framing: statements about voting/elections info, Ja/Nein"),
    ("model_test", 18, "Lesen", 4, "questions", "5 Ja/Nein statements"),
    ("model_test", 18, "Lesen", 4, "answer_options", "Ja/Nein checkboxes"),
    ("model_test", 19, "Lesen", 4, "source_text", "Structured info table: Wahlen/Abstimmungen (voting procedures/dates)"),
    ("model_test", 20, "Lesen", None, "metadata", "Blank (page footer only)"),
    ("model_test", 21, "Schreiben", None, "section_header", "'Schreiben / 1 Aufgabe / 25 Minuten'"),
    ("model_test", 22, "Schreiben", 1, "writing_prompt", "Write an invitation (Apéro) to colleagues; ~40 words, 3 required content points"),
    ("model_test", 23, "Schreiben", 1, "response_area", "Blank lines for candidate's own writing (no exam content)"),
    ("model_test", 24, "back", None, "metadata", "Grading/stamp page (Testanbieter, Korrektor/in, Datum)"),
    # Answer key document
    ("answer_key", 1, "Hoeren", 1, "answer_key", "Falsch/Richtig/Richtig/Falsch"),
    ("answer_key", 1, "Hoeren", 2, "answer_key", "Falsch/Richtig/Falsch"),
    ("answer_key", 1, "Hoeren", 3, "answer_key", "Falsch/Richtig/Richtig"),
    ("answer_key", 1, "Hoeren", 4, "answer_key", "Falsch/Richtig/Richtig"),
    ("answer_key", 2, "Lesen", 1, "answer_key", "2/1/2/3/1/2/3"),
    ("answer_key", 2, "Lesen", 2, "answer_key", "1/2/1/1/2/3"),
    ("answer_key", 2, "Lesen", 3, "answer_key", "D/F/B/C/H (situations 1-5)"),
    ("answer_key", 2, "Lesen", 4, "answer_key", "Nein/Nein/Nein/Ja/Ja"),
]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["doc", "page", "section", "aufgabe", "content_class", "description"])
        writer.writerows(ROWS)
    print(f"Wrote {len(ROWS)} rows to {OUT}")


if __name__ == "__main__":
    main()

"""Extract the alphabetical word list from Goethe A1/A2/B1 Wortliste PDFs.

Two different extraction strategies are used, because the PDFs use two
genuinely different physical layouts (verified via font/position
inspection on 2026-08-19):

A1 ("goethe_a1_wortliste.pdf"): single column per page, entries at left
margin x0~=143pt, one entry per line unless the example sentence wraps
(wrapped continuation indented to x0~=236.5pt). Parsed line-by-line with
a headword/marker/example heuristic -- see parse_entry_line().

A2/B1: two macro-columns per page (left half, right half), and *within*
each macro-column a further two-way split between a narrow "headword +
principal-parts/forms" sub-flow (e.g. x0 314.6-400 in the right
macro-column on a representative B1 page) and a wider "example sentence"
sub-flow (x0 421+) that wrap *independently* -- confirmed by inspecting
individual word x0/top coordinates for several multi-line verb entries
(e.g. "abschreiben, schreibt ab, / schrieb ab, / hat abgeschrieben" in the
forms sub-flow, interleaved row-by-row with "Er hat die Hausaufgaben von
mir / abgeschrieben." in the example sub-flow). Reconstructing full
entry-to-example alignment for this nested-column dictionary layout is a
non-trivial table-extraction problem; the CEFR-membership use case this
project actually needs (Phase 5: "In A1 list -> A1; not A1 but in A2 list
-> A2 ...") only requires the *set of headwords*, not examples. So for
A2/B1 this script extracts headwords only, via regex pattern-matching
over each macro-column's linearized text (order-independent within a
local 2-4 token window, which survives the sub-flow interleaving even
though full sentences do not). This under-recalls bare adjectives/adverbs
that carry no article or verb-comma marker (documented limitation, see
reports/goethe_extraction_notes.md) -- nouns and verbs, the majority of
entries, are captured reliably.
"""
import csv
import re
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "goethe"
INTERIM = ROOT / "data" / "interim"
INTERIM.mkdir(parents=True, exist_ok=True)

ARTICLES = {"der", "die", "das", "der/die", "die/der", "(der)", "(die)", "(das)"}
MARKER_RE = re.compile(r"^[-=][a-zäöüßA-ZÄÖÜ]{0,6},?$|^[a-zäöüß]{1,3},?$")
SECTION_HEADER_RE = re.compile(r"^[A-ZÄÖÜ]$")

# CEFR level implied by filename; used only for provenance tagging in output.
LEVEL_BY_FILE = {
    "goethe_a1_wortliste.pdf": "A1",
    "goethe_a2_wortliste.pdf": "A2",
    "goethe_b1_wortliste.pdf": "B1",
}


def get_lines(page):
    """Group words into reading-order lines, excluding watermark/footer noise."""
    words = page.extract_words(extra_attrs=["upright"])
    content_words = [
        w
        for w in words
        if w.get("upright", True)
        and w["x0"] >= 130
        and w["top"] < (page.height - 35)
    ]
    lines = {}
    for w in content_words:
        key = round(w["top"])
        lines.setdefault(key, []).append(w)
    out = []
    for top in sorted(lines.keys()):
        ws = sorted(lines[top], key=lambda w: w["x0"])
        out.append({"top": top, "x0": ws[0]["x0"], "words": ws, "text": " ".join(w["text"] for w in ws)})
    return out


def parse_entry_line(text: str):
    tokens = text.split()
    idx = 0
    article = None
    if tokens and tokens[0] in ARTICLES:
        article = tokens[0]
        idx = 1
    if idx >= len(tokens):
        return None
    headword = tokens[idx].rstrip(",")
    headword_had_comma = tokens[idx].endswith(",")
    idx += 1
    markers = []
    quality_flag = ""
    if headword_had_comma:
        while idx < len(tokens) and MARKER_RE.match(tokens[idx]):
            markers.append(tokens[idx].rstrip(","))
            idx += 1
    example = " ".join(tokens[idx:])
    if not example or not example[0].isupper():
        quality_flag = "unparsed_example_boundary"
    return {
        "article": article or "",
        "headword": headword,
        "plural_or_forms": ",".join(markers),
        "example": example,
        "quality_flag": quality_flag,
    }


NOUN_HEADWORD_RE = re.compile(
    r"\b(der/die|die/der|der|die|das)\s+([A-ZÄÖÜ][a-zA-ZäöüÄÖÜß\-]+)(,\s*[¨\-=]?[a-zA-Zäöüß\-]{1,4})?"
)
VERB_HEADWORD_RE = re.compile(
    r"\b([a-zäöüß]{3,}(?:en|eln|ern)),\s+[a-zäöüß]"
)
# Each macro-column (left half-page, right half-page) has its own nested
# "forms" sub-flow (headwords/principal-parts, narrow, near the macro-column's
# left edge) and "example" sub-flow (wider, to its right). Restricting the
# headword regex scan to the forms sub-flow avoids false-positive article
# matches from dative/genitive "der"/"die" inside example-sentence prepositional
# phrases (e.g. "mit der Bahn" wrongly read as article "der" + noun "Bahn").
FORMS_SUBCOLUMNS = [(20, 131), (280, 410)]


def extract_headwords_two_column(pdf_path: Path, level: str):
    """Headword-only extraction for the nested two-sub-column A2/B1 layout."""
    rows = []
    seen = set()
    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages, start=1):
            words = page.extract_words(extra_attrs=["upright"])
            for lo, hi in FORMS_SUBCOLUMNS:
                col_words = [
                    w
                    for w in words
                    if w.get("upright", True)
                    and lo <= w["x0"] < hi
                    and w["top"] < (page.height - 35)
                ]
                if not col_words:
                    continue
                lines = {}
                for w in col_words:
                    lines.setdefault(round(w["top"]), []).append(w)
                text = " ".join(
                    " ".join(w["text"] for w in sorted(lines[top], key=lambda w: w["x0"]))
                    for top in sorted(lines.keys())
                )

                for m in NOUN_HEADWORD_RE.finditer(text):
                    article, headword, marker = m.group(1), m.group(2), m.group(3) or ""
                    key = (article, headword)
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append(
                        {
                            "level": level,
                            "page": page_idx,
                            "article": article,
                            "headword": headword,
                            "plural_or_forms": marker.lstrip(", ") if marker else "",
                            "example": "",
                            "quality_flag": "headword_only_no_example",
                            "raw_line": m.group(0),
                        }
                    )
                for m in VERB_HEADWORD_RE.finditer(text):
                    headword = m.group(1)
                    key = ("", headword)
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append(
                        {
                            "level": level,
                            "page": page_idx,
                            "article": "",
                            "headword": headword,
                            "plural_or_forms": "",
                            "example": "",
                            "quality_flag": "headword_only_no_example",
                            "raw_line": m.group(0),
                        }
                    )
    return rows


def extract_file(pdf_path: Path, level: str):
    entries = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages, start=1):
            for line in get_lines(page):
                text = line["text"].strip()
                if not text or text == "INVeNTAre":
                    continue
                if SECTION_HEADER_RE.match(text):
                    continue
                is_entry_start = 141 <= line["x0"] <= 146
                is_continuation = 234 <= line["x0"] <= 240
                if is_entry_start:
                    parsed = parse_entry_line(text)
                    if parsed is None:
                        continue
                    parsed["page"] = page_idx
                    parsed["level"] = level
                    parsed["raw_line"] = text
                    entries.append(parsed)
                elif is_continuation and entries:
                    entries[-1]["example"] = (entries[-1]["example"] + " " + text).strip()
                    entries[-1]["raw_line"] += " | " + text
                # else: unrecognized indentation (e.g. Wortgruppenliste section,
                # front matter) -- intentionally skipped, not part of the
                # alphabetic headword-level list this script targets.
    return entries


def main():
    all_rows = []
    for fname, level in LEVEL_BY_FILE.items():
        path = RAW / fname
        if level == "A1":
            entries = extract_file(path, level)
        else:
            entries = extract_headwords_two_column(path, level)
        flagged = sum(1 for e in entries if e["quality_flag"])
        print(f"{fname}: {len(entries)} entries extracted, {flagged} flagged ({flagged/len(entries):.1%})")
        all_rows.extend(entries)

    out_path = INTERIM / "goethe_wortlisten_extracted.csv"
    fieldnames = ["level", "page", "article", "headword", "plural_or_forms", "example", "quality_flag", "raw_line"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\nWrote {len(all_rows)} total entries -> {out_path}")


if __name__ == "__main__":
    main()

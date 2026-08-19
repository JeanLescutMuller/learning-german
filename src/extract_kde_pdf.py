"""Extract text (with layout) from the official KDE model test and answer key PDFs.

Writes one JSON file per source PDF to data/interim/, one record per page:
{page_number, text, words: [{text, x0, x1, top, bottom}]}.

This is raw extraction only -- no section/task boundaries are inferred here.
Section mapping is a separate, manually-checked step (see data/interim/
kde_model_test_section_map.csv), because page-based text order does not
reliably distinguish instructions from source text from answer options
without visual/manual judgment (CLAUDE.md: "Do not conflate exam
instructions, source passages and answer options.").
"""
import json
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "kde_official"
INTERIM = ROOT / "data" / "interim"
INTERIM.mkdir(parents=True, exist_ok=True)

TARGETS = [
    "kde_modell_test.pdf",
    "kde_modell_test_loesungsschluessel.pdf",
]


def extract(pdf_path: Path) -> list[dict]:
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            words = page.extract_words()
            pages.append(
                {
                    "page_number": i,
                    "width": page.width,
                    "height": page.height,
                    "text": text,
                    "words": [
                        {
                            "text": w["text"],
                            "x0": round(w["x0"], 1),
                            "x1": round(w["x1"], 1),
                            "top": round(w["top"], 1),
                            "bottom": round(w["bottom"], 1),
                        }
                        for w in words
                    ],
                }
            )
    return pages


def main() -> None:
    for name in TARGETS:
        src = RAW / name
        pages = extract(src)
        out = INTERIM / (src.stem + "_extracted.json")
        out.write_text(json.dumps(pages, ensure_ascii=False, indent=1), encoding="utf-8")
        n_words = sum(len(p["words"]) for p in pages)
        print(f"{name}: {len(pages)} pages, {n_words} words -> {out}")


if __name__ == "__main__":
    main()

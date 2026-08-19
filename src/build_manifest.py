"""Build source_manifest.csv from data/raw/, computing SHA-256 for every file.

Run after adding/updating files in data/raw/. Manifest rows are hand-authored
metadata (URL, publisher, license, retrieval date) looked up by relative path;
the script fills in size and checksum automatically and fails loudly if a raw
file has no matching metadata entry (provenance must never be silently missing).
"""
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MANIFEST_PATH = ROOT / "source_manifest.csv"

RETRIEVED = "2026-08-19"

# path relative to data/raw/ -> metadata
SOURCES = {
    "kde_official/kde_modell_test.pdf": dict(
        url="https://www.zh.ch/content/dam/zhweb/bilder-dokumente/themen/migration-integration/einbuergerung/kde/kde_modell_test.pdf",
        publisher="Kanton Zurich (Sicherheitsdirektion / Migrationsamt)",
        title="KDE Modelltest (official 24-page written model test)",
        version_date="undated on document; retrieved 2026-08-19",
        license_terms="Official public exam-preparation material; personal/study use. No redistribution-at-scale confirmed.",
        intended_use="Phase 1: KDE annotated corpus, lexical difficulty analysis",
        processing_script="src/extract_kde_pdf.py",
        notes="CLAUDE.md URL used 'einbuerung' (typo); live site uses 'einbuergerung'. Corrected.",
    ),
    "kde_official/kde_modell_test_loesungsschluessel.pdf": dict(
        url="https://www.zh.ch/content/dam/zhweb/bilder-dokumente/themen/migration-integration/einbuergerung/kde/kde_modell_test_loesungsschluessel.pdf",
        publisher="Kanton Zurich",
        title="KDE Modelltest - Loesungsschluessel (official answer key)",
        version_date="undated on document; retrieved 2026-08-19",
        license_terms="Official public exam-preparation material; personal/study use.",
        intended_use="Phase 1/4: answer verification for KDE model test annotation",
        processing_script="src/extract_kde_pdf.py",
        notes="",
    ),
    "kde_official/reglement_gemeinden_testanbieter_kde_okt_2021.pdf": dict(
        url="https://www.zh.ch/content/dam/zhweb/bilder-dokumente/themen/migration-integration/einbuergerung/kde/reglement_gemeinden_testanbieter_kde_okt_2021.pdf",
        publisher="Kanton Zurich",
        title="Reglement fuer Gemeinden und Testanbieter KDE (Oct 2021)",
        version_date="2021-10",
        license_terms="Official public regulation document.",
        intended_use="Phase 0/4: encode official test structure, timing, pass thresholds",
        processing_script="src/extract_kde_pdf.py",
        notes="",
    ),
    "kde_official/richtlinien_testanbieter_kde_okt_2021.pdf": dict(
        url="https://www.zh.ch/content/dam/zhweb/bilder-dokumente/themen/migration-integration/einbuergerung/kde/richtlinien_testanbieter_kde_okt_2021.pdf",
        publisher="Kanton Zurich",
        title="Richtlinien fuer Testanbieter KDE (Oct 2021)",
        version_date="2021-10",
        license_terms="Official public regulation document.",
        intended_use="Phase 0: supplementary exam administration rules",
        processing_script="(not yet processed)",
        notes="Not listed explicitly in CLAUDE.md reference list; discovered via live site alongside reglement doc.",
    ),
    "kde_official/vereinbarung_vorlage_kde_2022.pdf": dict(
        url="https://www.zh.ch/content/dam/zhweb/bilder-dokumente/themen/migration-integration/einbuergerung/kde/vereinbarung_vorlage_kde_2022.pdf",
        publisher="Kanton Zurich",
        title="Vereinbarung Vorlage KDE 2022 (template agreement)",
        version_date="2022",
        license_terms="Official public template document.",
        intended_use="Phase 0: reference only, administrative context",
        processing_script="(not processed - administrative template, low relevance)",
        notes="Not listed in CLAUDE.md reference list; discovered via live site.",
    ),
    "kde_official/kde_modell_test_hoeren.mp3": dict(
        url="https://www.zh.ch/content/dam/zhweb/bilder-dokumente/themen/migration-integration/einbuergerung/kde/kde_modell_test_hoeren.mp3",
        publisher="Kanton Zurich",
        title="KDE Modelltest - Hoeren (official listening audio)",
        version_date="undated on document; retrieved 2026-08-19",
        license_terms="Official public exam-preparation material; personal/study use.",
        intended_use="Phase 1 (deferred): local transcription, listening-section vocabulary analysis",
        processing_script="(not yet processed - transcription deferred to later session)",
        notes="Contains at least one Swiss-German segment per CLAUDE.md; do not treat automatic transcription as authoritative.",
    ),
    "goethe/goethe_a1_wortliste.pdf": dict(
        url="https://www.goethe.de/pro/relaunch/prf/de/A1_SD1_Wortliste_02.pdf",
        publisher="Goethe-Institut",
        title="Goethe-Zertifikat A1 (Start Deutsch 1) Wortliste",
        version_date="undated on document; retrieved 2026-08-19",
        license_terms="Copyrighted Goethe-Institut exam material. Store derived membership flags only; do not redistribute full list text.",
        intended_use="Phase 2/3/5: CEFR A1 membership for derived_cefr_band",
        processing_script="src/extract_goethe_pdf.py",
        notes="",
    ),
    "goethe/goethe_a2_wortliste.pdf": dict(
        url="https://www.goethe.de/pro/relaunch/prf/de/Goethe-Zertifikat_A2_Wortliste.pdf",
        publisher="Goethe-Institut",
        title="Goethe-Zertifikat A2 Wortliste",
        version_date="undated on document; retrieved 2026-08-19",
        license_terms="Copyrighted Goethe-Institut exam material. Store derived membership flags only; do not redistribute full list text.",
        intended_use="Phase 2/3/5: CEFR A2 membership for derived_cefr_band",
        processing_script="src/extract_goethe_pdf.py",
        notes="",
    ),
    "goethe/goethe_b1_wortliste.pdf": dict(
        url="https://www.goethe.de/pro/relaunch/prf/de/Goethe-Zertifikat_B1_Wortliste.pdf",
        publisher="Goethe-Institut / OeSD / Universitaet Freiburg",
        title="Goethe-Zertifikat B1 Wortliste",
        version_date="undated on document; retrieved 2026-08-19",
        license_terms="Copyrighted Goethe-Institut exam material. Store derived membership flags only; do not redistribute full list text.",
        intended_use="Phase 2/3/5: CEFR B1 membership for derived_cefr_band. ~2400 lexical units, pluricentric (includes Swiss variants e.g. parkieren).",
        processing_script="src/extract_goethe_pdf.py",
        notes="",
    ),
    "subtlex_de/subtlex_de_cleaned_zipf.xlsx": dict(
        url="https://osf.io/download/y6ebr/ (resolved via OSF API from project py9ba, linked from paper landing page https://osf.io/download/ayh2q)",
        publisher="Brysbaert, Buchmeier, Conrad, Jacobs, Boelte, Boehl (OSF project py9ba)",
        title="SUBTLEX-DE cleaned version with Zipf values.xlsx",
        version_date="dataset modified 2021-02-01 (file timestamp); retrieved 2026-08-19",
        license_terms="CC BY-NC-SA 4.0 (see data/raw/subtlex_de/license.txt). Non-commercial use only; attribution required; share-alike.",
        intended_use="Phase 3: Tier 2 conversational/subtitle frequency (frequency_subtlex_raw/per_million/zipf)",
        processing_script="src/extract_subtlex.py",
        notes="Verified via MD5 checksum match (2e65fd03e5972686141a1c3546c095a2) against OSF API metadata. This is the actual data file; the CLAUDE.md-provided URL (osf.io/download/ayh2q) resolves to the *paper PDF*, not the dataset -- both downloaded and cross-linked here.",
    ),
    "subtlex_de/brysbaert_et_al_2011_subtlex-de.pdf": dict(
        url="https://osf.io/download/ayh2q",
        publisher="Brysbaert, Buchmeier, Conrad, Jacobs, Boelte, Boehl",
        title="Brysbaert et al. 2011 - SUBTLEX-DE (paper)",
        version_date="2011; retrieved 2026-08-19",
        license_terms="Published paper; see OSF project for terms. Reference only.",
        intended_use="Documentation: methodology reference for SUBTLEX-DE fields/construction",
        processing_script="(reference document, not parsed for data)",
        notes="This is the URL literally given in CLAUDE.md; it points to the paper, not the frequency dataset.",
    ),
    "subtlex_de/license.txt": dict(
        url="https://osf.io/download/ua8mj/",
        publisher="OSF project py9ba",
        title="SUBTLEX-DE license.txt",
        version_date="2024-05-07 (file timestamp); retrieved 2026-08-19",
        license_terms="CC BY-NC-SA 4.0 (self-describing)",
        intended_use="License documentation for subtlex_de_cleaned_zipf.xlsx",
        processing_script="(reference document)",
        notes="",
    ),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    rows = []
    raw_files = sorted(p for p in RAW.rglob("*") if p.is_file())
    seen = set()

    for path in raw_files:
        rel = str(path.relative_to(RAW))
        seen.add(rel)
        meta = SOURCES.get(rel)
        if meta is None:
            raise SystemExit(
                f"FATAL: {rel} exists in data/raw/ but has no metadata entry in "
                f"src/build_manifest.py:SOURCES. Every raw file must have documented provenance."
            )
        rows.append(
            {
                "relative_path": f"data/raw/{rel}",
                "url": meta["url"],
                "publisher": meta["publisher"],
                "title": meta["title"],
                "version_date": meta["version_date"],
                "retrieval_timestamp_utc": RETRIEVED,
                "file_size_bytes": path.stat().st_size,
                "sha256": sha256(path),
                "license_terms": meta["license_terms"],
                "intended_use": meta["intended_use"],
                "processing_script": meta["processing_script"],
                "notes": meta["notes"],
            }
        )

    missing = set(SOURCES) - seen
    if missing:
        raise SystemExit(f"FATAL: manifest declares files not found on disk: {missing}")

    with open(MANIFEST_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()

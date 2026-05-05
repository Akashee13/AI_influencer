#!/usr/bin/env python3
"""Scan a QA gap report and compare its gaps against existing spec artifacts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
REPORTS_DIR = ROOT / "docs" / "gap-finding"
SPECS_DIR = ROOT / "specs"

STOPWORDS = {
    "about",
    "after",
    "again",
    "align",
    "along",
    "already",
    "also",
    "before",
    "being",
    "between",
    "blocked",
    "cannot",
    "completed",
    "confirm",
    "current",
    "default",
    "different",
    "during",
    "error",
    "failed",
    "failure",
    "first",
    "follow",
    "gateway",
    "image",
    "images",
    "issue",
    "local",
    "model",
    "output",
    "outputs",
    "partial",
    "path",
    "paths",
    "report",
    "result",
    "runtime",
    "scene",
    "should",
    "spec",
    "still",
    "than",
    "that",
    "their",
    "there",
    "these",
    "this",
    "through",
    "using",
    "verify",
    "visual",
    "workflow",
    "would",
}


def latest_report_path() -> Path:
    reports = sorted(REPORTS_DIR.glob("*/report.md"))
    if not reports:
        raise FileNotFoundError(f"no reports found under {REPORTS_DIR}")
    return reports[-1]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def extract_section(markdown: str, heading: str) -> str:
    pattern = rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, markdown, flags=re.M | re.S)
    return match.group(1).strip() if match else ""


def extract_candidates(section_text: str) -> list[str]:
    lines = []
    for raw_line in section_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^[-*]\s+", "", line)
        if line and line != "None provided.":
            lines.append(line)
    return lines


def keywords(text: str) -> list[str]:
    words = []
    seen = set()
    for token in normalize(text).split():
        if len(token) < 4 or token in STOPWORDS:
            continue
        if token not in seen:
            seen.add(token)
            words.append(token)
    return words[:8]


def iter_spec_files() -> list[Path]:
    return sorted(path for path in SPECS_DIR.glob("*/*.md") if path.is_file())


def load_spec_corpus() -> list[tuple[Path, str]]:
    corpus = []
    for path in iter_spec_files():
        corpus.append((path, normalize(path.read_text())))
    return corpus


def covered_by_specs(text: str, corpus: list[tuple[Path, str]]) -> list[str]:
    text_norm = normalize(text)
    keys = keywords(text)
    matches: list[str] = []

    for path, doc in corpus:
        if text_norm and text_norm in doc:
            matches.append(str(path.relative_to(ROOT)))
            continue

        if not keys:
            continue

        overlap = sum(1 for key in keys if key in doc)
        threshold = max(2, len(keys) - 1)
        if overlap >= threshold:
            matches.append(str(path.relative_to(ROOT)))

    return matches


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan a QA report for likely new gaps.")
    parser.add_argument("--report", help="Path to report.md. Defaults to the latest docs/gap-finding report.")
    args = parser.parse_args()

    report_path = Path(args.report).resolve() if args.report else latest_report_path()
    markdown = report_path.read_text()
    corpus = load_spec_corpus()

    sections = {
        "Top Gaps": extract_candidates(extract_section(markdown, "Top Gaps")),
        "Recommended Fixes": extract_candidates(extract_section(markdown, "Recommended Fixes")),
    }

    findings = []
    for section_name, lines in sections.items():
        for line in lines:
            matches = covered_by_specs(line, corpus)
            findings.append(
                {
                    "section": section_name,
                    "text": line,
                    "keywords": keywords(line),
                    "covered_by": matches,
                    "is_new": not matches,
                }
            )

    payload = {
        "report_path": str(report_path.relative_to(ROOT)),
        "new_gap_count": sum(1 for item in findings if item["is_new"]),
        "findings": findings,
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

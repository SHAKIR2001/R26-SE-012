"""Reconstruct page-level DEA EAC pepper observations without imputing prices."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
INDEX_URL = "https://exagri.info/mkt/index.html"
RETRIEVAL_DATE = date.today().isoformat()
USER_AGENT = "MultimodalPepperAI-Research/Phase4 (academic price reconstruction)"
RAW_DIR = ROOT / "data/raw/market_prices/eac_phase4"
PAGE_CACHE_DIR = RAW_DIR / "pages"
OUT_DIR = ROOT / "data/processed/grading_forecast/price/eac_reconstructed_v1"
INDEX_SNAPSHOT = RAW_DIR / f"dea_eac_index_{RETRIEVAL_DATE}.html"
RAW_CSV = RAW_DIR / f"dea_eac_pepper_observations_retrieved_{RETRIEVAL_DATE}.csv"
SOURCE_MANIFEST = OUT_DIR / "eac_pepper_price_source_manifest.csv"


class PepperTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.pepper_anchor_seen = False
        self.in_target_table = False
        self.target_table_complete = False
        self.table_depth = 0
        self.in_cell = False
        self.cell_parts: list[str] = []
        self.current_row: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag.lower() == "a" and (attrs_dict.get("name") or "").lower() == "pepper":
            self.pepper_anchor_seen = True
        if tag.lower() == "table":
            if self.pepper_anchor_seen and not self.in_target_table and not self.target_table_complete:
                self.in_target_table = True
                self.table_depth = 1
            elif self.in_target_table:
                self.table_depth += 1
        if self.in_target_table and tag.lower() in {"td", "th"}:
            self.in_cell = True
            self.cell_parts = []
        if self.in_target_table and tag.lower() == "tr":
            self.current_row = []

    def handle_endtag(self, tag: str) -> None:
        if self.in_target_table and tag.lower() in {"td", "th"} and self.in_cell:
            value = re.sub(r"\s+", " ", html.unescape("".join(self.cell_parts))).strip()
            self.current_row.append(value)
            self.in_cell = False
        if self.in_target_table and tag.lower() == "tr" and self.current_row:
            self.rows.append(self.current_row)
            self.current_row = []
        if self.in_target_table and tag.lower() == "table":
            self.table_depth -= 1
            if self.table_depth == 0:
                self.in_target_table = False
                self.target_table_complete = True

    def handle_data(self, data: str) -> None:
        if self.in_target_table and self.in_cell:
            self.cell_parts.append(data)


def fetch(url: str, *, attempts: int = 8) -> bytes:
    for attempt in range(attempts):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError, ssl.SSLError, ConnectionError, OSError):
            if attempt == attempts - 1:
                raise
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError("unreachable fetch retry state")


def dated_page_urls(index_payload: bytes) -> list[tuple[date, str]]:
    text = index_payload.decode("utf-8", errors="replace")
    hrefs = re.findall(r'href\s*=\s*["\']([^"\']+\.html)["\']', text, flags=re.I)
    found: dict[date, str] = {}
    for href in hrefs:
        match = re.search(r"(?:(\d{4})/)?(\d{1,2})\.(\d{1,2})\.(\d{4})\.html$", href)
        if not match:
            continue
        day, month, year = int(match.group(2)), int(match.group(3)), int(match.group(4))
        page_date = date(year, month, day)
        url = urllib.parse.urljoin(INDEX_URL, href)
        if match.group(1) is None:
            url = urllib.parse.urljoin(INDEX_URL, f"{year}/{day:02d}.{month:02d}.{year}.html")
        found[page_date] = url
    return sorted(found.items())


def parse_price(value: str) -> float | None:
    clean = value.replace(",", "").strip()
    if clean in {"", "-", "–", "—", "N/A", "n/a"}:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", clean)
    return float(match.group()) if match else None


def normalize_district(value: str) -> str:
    clean = re.sub(r"\s+", " ", value.replace("_", " ").strip())
    return "Nuwara Eliya" if clean.lower() == "nuwara eliya" else clean.title()


def parse_page(page_date: date, url: str, payload: bytes) -> tuple[list[dict], dict]:
    parser = PepperTableParser()
    parser.feed(payload.decode("utf-8", errors="replace"))
    digest = hashlib.sha256(payload).hexdigest()
    observations: list[dict] = []
    missing = {"Grade 1 highest": 0, "Grade 1 average": 0, "Grade 2 highest": 0, "Grade 2 average": 0}
    data_rows = [row for row in parser.rows if len(row) >= 5 and row[0].strip().lower() != "district"]
    for row in data_rows:
        district = normalize_district(row[0])
        if not district:
            continue
        values = [parse_price(value) for value in row[1:5]]
        for (grade, price_type), price in zip(
            (("Grade 1", "highest"), ("Grade 1", "average"), ("Grade 2", "highest"), ("Grade 2", "average")),
            values,
            strict=True,
        ):
            if price is None:
                missing[f"{grade} {price_type}"] += 1
                continue
            observations.append({
                "date": page_date.isoformat(), "market": district, "commodity": "black_pepper",
                "grade": grade, "price_type": price_type, "price_lkr_per_kg": price,
                "source": "Department of Export Agriculture, Sri Lanka - Economic Research Unit",
                "source_url": url, "source_date": page_date.isoformat(), "retrieval_date": RETRIEVAL_DATE,
                "country": "Sri Lanka", "currency": "LKR", "unit": "kg", "market_level": "farm_gate",
                "source_frequency_label": "weekly", "source_page_sha256": digest,
            })
    status = "parsed" if observations else "no_pepper_observations"
    return observations, {
        "source_date": page_date.isoformat(), "source_url": url, "retrieval_date": RETRIEVAL_DATE,
        "http_status": 200, "page_sha256": digest, "page_bytes": len(payload), "parse_status": status,
        "pepper_table_rows": len(data_rows), "observations_extracted": len(observations),
        "missing_grade1_highest_cells": missing["Grade 1 highest"],
        "missing_grade1_average_cells": missing["Grade 1 average"],
        "missing_grade2_highest_cells": missing["Grade 2 highest"],
        "missing_grade2_average_cells": missing["Grade 2 average"], "error": "",
    }


def retrieve_one(item: tuple[date, str]) -> tuple[list[dict], dict]:
    page_date, url = item
    cache_path = PAGE_CACHE_DIR / str(page_date.year) / f"{page_date.strftime('%d.%m.%Y')}.html"
    try:
        if cache_path.is_file():
            payload = cache_path.read_bytes()
        else:
            payload = fetch(url)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(payload)
        observations, manifest = parse_page(page_date, url, payload)
        manifest["local_page_path"] = str(cache_path.relative_to(ROOT)).replace("\\", "/")
        return observations, manifest
    except Exception as exc:  # noqa: BLE001
        http_status = exc.code if isinstance(exc, urllib.error.HTTPError) else ""
        return [], {
            "source_date": page_date.isoformat(), "source_url": url, "retrieval_date": RETRIEVAL_DATE,
            "http_status": http_status, "page_sha256": "", "page_bytes": 0,
            "parse_status": "broken_index_link" if http_status == 404 else "error",
            "pepper_table_rows": 0, "observations_extracted": 0,
            "missing_grade1_highest_cells": 0, "missing_grade1_average_cells": 0,
            "missing_grade2_highest_cells": 0, "missing_grade2_average_cells": 0,
            "error": f"{type(exc).__name__}: {exc}", "local_page_path": "",
        }


def main() -> int:
    index_payload = fetch(INDEX_URL)
    pages = dated_page_urls(index_payload)
    if len(pages) < 400:
        raise RuntimeError(f"Expected broad DEA history, found only {len(pages)} dated pages")
    all_observations: list[dict] = []
    manifest_rows: list[dict] = []
    PAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(retrieve_one, item) for item in pages]
        for count, future in enumerate(as_completed(futures), start=1):
            observations, page_manifest = future.result()
            all_observations.extend(observations)
            manifest_rows.append(page_manifest)
            if count % 50 == 0:
                print(f"Retrieved {count}/{len(pages)} dated pages")
    errors = [row for row in manifest_rows if row["parse_status"] == "error"]
    broken_links = [row for row in manifest_rows if row["parse_status"] == "broken_index_link"]
    if errors:
        raise RuntimeError(f"{len(errors)} non-404 source pages failed; first: {errors[0]}")

    key_fields = ["date", "market", "grade", "price_type"]
    unique: dict[tuple, dict] = {}
    conflicts: list[dict] = []
    for row in sorted(all_observations, key=lambda r: (r["date"], r["market"], r["grade"], r["price_type"])):
        key = tuple(row[field] for field in key_fields)
        if key in unique and unique[key]["price_lkr_per_kg"] != row["price_lkr_per_kg"]:
            conflicts.append({"key": key, "first": unique[key], "second": row})
        unique.setdefault(key, row)
    if conflicts:
        raise RuntimeError(f"Conflicting duplicate source observations: {conflicts[:2]}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_SNAPSHOT.write_bytes(index_payload)
    observation_fields = [
        "date", "market", "commodity", "grade", "price_type", "price_lkr_per_kg", "source", "source_url",
        "source_date", "retrieval_date", "country", "currency", "unit", "market_level", "source_frequency_label",
        "source_page_sha256",
    ]
    with RAW_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=observation_fields)
        writer.writeheader()
        writer.writerows(unique.values())
    sorted_manifest = sorted(manifest_rows, key=lambda r: r["source_date"])
    with SOURCE_MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sorted_manifest[0]))
        writer.writeheader()
        writer.writerows(sorted_manifest)

    summary = {
        "retrieval_date": RETRIEVAL_DATE, "index_url": INDEX_URL, "index_sha256": hashlib.sha256(index_payload).hexdigest(),
        "dated_pages": len(pages), "pages_with_pepper_observations": sum(r["parse_status"] == "parsed" for r in manifest_rows),
        "pages_without_pepper_observations": sum(r["parse_status"] == "no_pepper_observations" for r in manifest_rows),
        "broken_index_links": len(broken_links),
        "broken_index_link_dates": [row["source_date"] for row in sorted(broken_links, key=lambda r: r["source_date"])],
        "page_errors": 0, "raw_observations": len(all_observations), "canonical_unique_observations": len(unique),
        "exact_duplicate_observations_removed": len(all_observations) - len(unique), "conflicting_duplicates": 0,
        "date_range": {"start": min(r["date"] for r in unique.values()), "end": max(r["date"] for r in unique.values())},
        "raw_csv": str(RAW_CSV.relative_to(ROOT)).replace("\\", "/"),
        "source_manifest": str(SOURCE_MANIFEST.relative_to(ROOT)).replace("\\", "/"),
    }
    (OUT_DIR / "reconstruction_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

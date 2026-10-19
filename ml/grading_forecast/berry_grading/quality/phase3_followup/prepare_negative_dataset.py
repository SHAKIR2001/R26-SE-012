"""Resume-safe Wikimedia negative acquisition, split, validation, and YOLO preparation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import random
import re
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[5]
API = "https://commons.wikimedia.org/w/api.php"
OPENVERSE_API = "https://api.openverse.org/v1/images/"
USER_AGENT = "MultimodalPepperAI-Research/Phase3Followup (educational research; contact repository owner)"
SEED = 42
MANIFEST = ROOT / "data/processed/grading_forecast/berry_v3/phase3_followup_negative_manifest.csv"
SUMMARY = ROOT / "data/processed/grading_forecast/berry_v3/phase3_followup_negative_dataset_summary.json"
DOWNLOAD_ROOT = ROOT / "data/external/phase3_followup_negatives"
FAILURES = DOWNLOAD_ROOT / "download_failures.jsonl"
YOLO_ROOT = ROOT / "data/processed/grading_forecast/berry_v3/phase3_followup_yolo"
V3_MANIFEST = ROOT / "data/processed/grading_forecast/berry_v3/v3_image_sample_manifest.csv"
PHASE3_MANIFEST = ROOT / "data/processed/grading_forecast/berry_v3/phase3_negative_manifest.csv"

CATEGORY_PLAN = {
    "vegetation_leaves": (90, ["green leaves closeup", "dry leaves plant", "mixed vegetation", "fern foliage", "pepper plant leaves", "tropical foliage", "garden plant leaves", "leaf litter closeup"]),
    "agricultural_crops": (75, ["rice plants field", "tea plantation leaves", "coffee plant crop", "maize plants", "vegetable crop field", "fruit crop plants", "wheat crop", "potato plants field"]),
    "aerial_crop_imagery": (60, ["aerial crop field", "drone farmland", "aerial plantation", "satellite agricultural fields", "aerial vegetation landscape", "terraced fields aerial"]),
    "agricultural_materials": (50, ["farm soil closeup", "harvest basket", "agricultural sacks", "farm tools", "plant debris", "compost pile", "farm surface"]),
    "other_spices_food": (60, ["dried spices", "coffee beans closeup", "dried beans", "grain seeds", "berries fruit closeup", "dried plant food", "cloves spice", "coriander seeds"]),
    "ordinary_objects": (45, ["hands object", "clothing closeup", "household container", "table tools", "people outdoors", "kitchen objects", "wooden objects"]),
    "background_scenes": (40, ["empty table surface", "farm background", "outdoor ground scene", "indoor empty scene", "forest ground", "plain floor surface"]),
}

FIELDS = [
    "negative_id", "category", "subcategory", "source", "source_page", "image_url",
    "creator", "license", "license_url", "source_group", "split", "original_filename",
    "local_path", "download_timestamp", "sha256", "width", "height", "bytes",
    "download_status", "notes",
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_html(value: str | None) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", value or "")).strip()


def api_request(params: dict) -> dict:
    url = API + "?" + urllib.parse.urlencode(params)
    last_error: Exception | None = None
    for attempt in range(6):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            last_error = exc
            time.sleep(min(30, 2 ** attempt))
    raise RuntimeError(f"Wikimedia API request failed after retries: {last_error}")


def search(query: str, offset: int = 0) -> list[dict]:
    payload = api_request({
        "action": "query", "format": "json", "formatversion": 2, "generator": "search",
        "gsrsearch": f"{query} filetype:bitmap", "gsrnamespace": 6, "gsrlimit": 50,
        "gsroffset": offset, "prop": "imageinfo", "iiprop": "url|mime|size|extmetadata",
        "iiurlwidth": 640,
    })
    return sorted(payload.get("query", {}).get("pages", []), key=lambda p: p.get("index", 999999))


def openverse_search(query: str, page: int = 1) -> list[dict]:
    params = urllib.parse.urlencode({"q": query, "license": "cc0,pdm,by,by-sa", "page_size": 50, "page": page})
    request = urllib.request.Request(OPENVERSE_API + "?" + params, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response).get("results", [])


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_manifest(rows: list[dict]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    temp = MANIFEST.with_suffix(".csv.tmp")
    with temp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: r["negative_id"]))
    temp.replace(MANIFEST)


def log_failure(payload: dict) -> None:
    DOWNLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    with FAILURES.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), **payload}, ensure_ascii=False) + "\n")


def forbidden_hashes() -> set[str]:
    hashes = {r["sha256"].lower() for r in read_csv(V3_MANIFEST) if r.get("sha256")}
    hashes.update(r["sha256"].lower() for r in read_csv(PHASE3_MANIFEST) if r.get("sha256"))
    return hashes


def validate_existing(rows: list[dict]) -> tuple[list[dict], set[str], set[str]]:
    valid, hashes, pages = [], set(), set()
    for row in rows:
        path = ROOT / row["local_path"]
        if row.get("download_status") != "usable" or not path.is_file():
            continue
        digest = sha256_file(path)
        if digest != row["sha256"]:
            raise RuntimeError(f"Cached file hash mismatch; refusing silent replacement: {path}")
        if digest in hashes:
            raise RuntimeError(f"Duplicate hash already present in follow-up manifest: {digest}")
        hashes.add(digest)
        pages.add(row["source_page"])
        valid.append(row)
    return valid, hashes, pages


def download(url: str) -> bytes:
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=90) as response:
                payload = response.read(12_000_001)
            if len(payload) > 12_000_000:
                raise ValueError("image_exceeds_12MB_limit")
            return payload
        except ValueError:
            raise
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                if attempt == 0:
                    last_error = exc
                    time.sleep(65.0)
                    continue
                raise RuntimeError(f"http_429_rate_limited_after_backoff: {exc}") from exc
            last_error = exc
            time.sleep(min(20, 2 ** attempt))
        except (OSError, urllib.error.URLError) as exc:
            last_error = exc
            time.sleep(min(20, 2 ** attempt))
    raise RuntimeError(str(last_error))


def image_metadata(payload: bytes) -> tuple[int, int, str]:
    with Image.open(io.BytesIO(payload)) as image:
        image.verify()
    with Image.open(io.BytesIO(payload)) as image:
        width, height = image.size
        fmt = (image.format or "").upper()
    if min(width, height) < 320:
        raise ValueError("minimum_dimension_below_320")
    if fmt not in {"JPEG", "PNG"}:
        raise ValueError(f"unsupported_format_{fmt}")
    return width, height, ".jpg" if fmt == "JPEG" else ".png"


def acquire(target_override: int | None = None) -> list[dict]:
    existing, seen_hashes, seen_pages = validate_existing(read_csv(MANIFEST))
    if FAILURES.exists():
        for line in FAILURES.read_text(encoding="utf-8").splitlines():
            try:
                failed_page = json.loads(line).get("source_page")
                if failed_page:
                    seen_pages.add(failed_page)
            except json.JSONDecodeError:
                continue
    forbidden = forbidden_hashes()
    rows = list(existing)
    creator_counts = Counter((r["creator"] or r["source_group"]).casefold() for r in rows)
    counts = Counter(r["category"] for r in rows)
    targets = {category: target for category, (target, _) in CATEGORY_PLAN.items()}
    if target_override:
        scale = target_override / sum(targets.values())
        targets = {k: max(1, round(v * scale)) for k, v in targets.items()}
    requested = sum(targets.values())
    rng = random.Random(SEED)
    category_order = sorted(CATEGORY_PLAN, key=lambda name: (counts[name] / targets[name], name))
    for category in category_order:
        _, queries = CATEGORY_PLAN[category]
        category_dir = DOWNLOAD_ROOT / category
        category_dir.mkdir(parents=True, exist_ok=True)
        query_cycle = list(queries)
        rng.shuffle(query_cycle)
        for query in query_cycle:
            if counts[category] >= targets[category]:
                break
            for offset in (0, 50, 100):
                if counts[category] >= targets[category]:
                    break
                try:
                    pages = search(query, offset)
                except Exception as exc:
                    log_failure({"category": category, "query": query, "stage": "search", "error": str(exc)})
                    continue
                for page in pages:
                    if counts[category] >= targets[category]:
                        break
                    info_items = page.get("imageinfo") or []
                    if not info_items:
                        continue
                    info = info_items[0]
                    title = page.get("title", "")
                    lowered = title.lower()
                    if any(term in lowered for term in ("black pepper", "peppercorn", "piper nigrum", "capsicum")):
                        continue
                    source_page = info.get("descriptionurl", "")
                    if not source_page or source_page in seen_pages:
                        continue
                    metadata = info.get("extmetadata", {})
                    creator = clean_html(metadata.get("Artist", {}).get("value"))
                    license_name = clean_html(metadata.get("LicenseShortName", {}).get("value"))
                    license_url = metadata.get("LicenseUrl", {}).get("value", "")
                    if not license_name or license_name.lower() in {"copyrighted", "fair use"}:
                        continue
                    group = creator.casefold() if creator else f"commons:{page.get('pageid', title)}"
                    if creator_counts[group] >= 3:
                        continue
                    # Use the API-provided 640-pixel thumbnail to limit shared
                    # service bandwidth. The canonical source page is retained.
                    image_url = info.get("thumburl") or info.get("url")
                    if not image_url:
                        continue
                    try:
                        payload = download(image_url)
                        digest = sha256_bytes(payload)
                        if digest in forbidden or digest in seen_hashes:
                            log_failure({"category": category, "query": query, "source_page": source_page, "stage": "deduplicate", "error": "duplicate_sha256"})
                            continue
                        width, height, extension = image_metadata(payload)
                    except Exception as exc:
                        log_failure({"category": category, "query": query, "source_page": source_page, "stage": "download_validate", "error": str(exc)})
                        continue
                    negative_id = f"p3fu_{category}_{counts[category] + 1:04d}"
                    path = category_dir / f"{negative_id}{extension}"
                    path.write_bytes(payload)
                    row = {
                        "negative_id": negative_id, "category": category, "subcategory": query,
                        "source": "Wikimedia Commons", "source_page": source_page, "image_url": image_url,
                        "creator": creator, "license": license_name, "license_url": license_url,
                        "source_group": group, "split": "UNASSIGNED", "original_filename": title.removeprefix("File:"),
                        "local_path": path.relative_to(ROOT).as_posix(),
                        "download_timestamp": datetime.now(timezone.utc).isoformat(), "sha256": digest,
                        "width": width, "height": height, "bytes": len(payload), "download_status": "usable", "notes": "",
                    }
                    rows.append(row)
                    seen_hashes.add(digest)
                    seen_pages.add(source_page)
                    creator_counts[group] += 1
                    counts[category] += 1
                    write_manifest(rows)
                    # Wikimedia is a shared public service. Pace media requests so a
                    # resumable research run does not become a bursty scraper.
                    time.sleep(1.0)
    print(f"Requested target={requested}; usable cached/downloaded={len(rows)}")
    return rows


def acquire_openverse(target_override: int | None = None) -> list[dict]:
    """Fill remaining category quotas from Openverse's open-license API."""
    existing, seen_hashes, seen_pages = validate_existing(read_csv(MANIFEST))
    forbidden = forbidden_hashes()
    rows = list(existing)
    creator_counts = Counter((r["creator"] or r["source_group"]).casefold() for r in rows)
    counts = Counter(r["category"] for r in rows)
    targets = {category: target for category, (target, _) in CATEGORY_PLAN.items()}
    if target_override:
        scale = target_override / sum(targets.values())
        targets = {k: max(1, round(v * scale)) for k, v in targets.items()}
    requested = sum(targets.values())
    category_order = sorted(CATEGORY_PLAN, key=lambda name: (counts[name] / targets[name], name))
    for category in category_order:
        _, queries = CATEGORY_PLAN[category]
        category_dir = DOWNLOAD_ROOT / category
        category_dir.mkdir(parents=True, exist_ok=True)
        for query in queries:
            if counts[category] >= targets[category]:
                break
            for page_number in (1, 2, 3):
                if counts[category] >= targets[category]:
                    break
                try:
                    candidates = openverse_search(query, page_number)
                except Exception as exc:
                    log_failure({"category": category, "query": query, "stage": "openverse_search", "error": str(exc)})
                    time.sleep(3.0)
                    continue
                for candidate in candidates:
                    if counts[category] >= targets[category]:
                        break
                    source_page = candidate.get("foreign_landing_url") or candidate.get("detail_url", "")
                    if not source_page or source_page in seen_pages or candidate.get("mature") is True:
                        continue
                    creator = clean_html(candidate.get("creator"))
                    source_name = candidate.get("source") or candidate.get("provider") or "unknown"
                    group = f"openverse:{source_name}:{creator.casefold() or candidate.get('id')}"
                    if creator_counts[group] >= 3:
                        continue
                    image_url = candidate.get("url") or candidate.get("thumbnail")
                    license_name = (candidate.get("license") or "").upper()
                    license_url = candidate.get("license_url") or ""
                    if not image_url or not license_name:
                        continue
                    try:
                        payload = download(image_url)
                        digest = sha256_bytes(payload)
                        if digest in forbidden or digest in seen_hashes:
                            log_failure({"category": category, "query": query, "source_page": source_page, "stage": "deduplicate", "error": "duplicate_sha256"})
                            continue
                        width, height, extension = image_metadata(payload)
                    except Exception as exc:
                        log_failure({"category": category, "query": query, "source_page": source_page, "stage": "openverse_download_validate", "error": str(exc)})
                        continue
                    negative_id = f"p3fu_{category}_{counts[category] + 1:04d}"
                    path = category_dir / f"{negative_id}{extension}"
                    path.write_bytes(payload)
                    row = {
                        "negative_id": negative_id, "category": category, "subcategory": query,
                        "source": f"Openverse/{source_name}", "source_page": source_page, "image_url": image_url,
                        "creator": creator, "license": license_name, "license_url": license_url,
                        "source_group": group, "split": "UNASSIGNED", "original_filename": clean_html(candidate.get("title")) or candidate.get("id", ""),
                        "local_path": path.relative_to(ROOT).as_posix(),
                        "download_timestamp": datetime.now(timezone.utc).isoformat(), "sha256": digest,
                        "width": width, "height": height, "bytes": len(payload), "download_status": "usable",
                        "notes": f"Openverse record {candidate.get('id', '')}; provider={candidate.get('provider', '')}",
                    }
                    rows.append(row); seen_hashes.add(digest); seen_pages.add(source_page)
                    creator_counts[group] += 1; counts[category] += 1
                    write_manifest(rows)
                    time.sleep(0.5)
    print(f"Openverse requested target={requested}; usable cached/downloaded={len(rows)}")
    return rows


def assign_splits(rows: list[dict]) -> list[dict]:
    by_group: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_group[row["source_group"]].append(row)
    totals = {"NEGATIVE_TRAIN": 0, "NEGATIVE_VALIDATION": 0, "NEGATIVE_FINAL_HOLDOUT": 0}
    ratios = {"NEGATIVE_TRAIN": 0.60, "NEGATIVE_VALIDATION": 0.20, "NEGATIVE_FINAL_HOLDOUT": 0.20}
    targets = {split: len(rows) * ratio for split, ratio in ratios.items()}
    category_totals = Counter(row["category"] for row in rows)
    category_counts: dict[str, Counter] = {split: Counter() for split in totals}
    groups = sorted(by_group.items(), key=lambda item: hashlib.sha256(f"{SEED}:{item[0]}".encode()).hexdigest())
    for _, group_rows in groups:
        group_categories = Counter(row["category"] for row in group_rows)
        def score(split: str) -> tuple[float, str]:
            global_load = (totals[split] + len(group_rows)) / targets[split]
            category_load = sum(
                (category_counts[split][category] + count) / max(1.0, category_totals[category] * ratios[split])
                for category, count in group_categories.items()
            ) / len(group_categories)
            return global_load + category_load, split
        chosen = min(totals, key=score)
        for row in group_rows:
            row["split"] = chosen
        totals[chosen] += len(group_rows)
        category_counts[chosen].update(group_categories)
    return rows


def copy_derived(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha256_file(destination) != sha256_file(source):
            raise RuntimeError(f"Derived image collision: {destination}")
        return
    # Use a real copy: Ultralytics may repair image files while scanning. A
    # hardlink would let that mutation propagate back into the provenance set.
    shutil.copy2(source, destination)


def prepare_yolo(rows: list[dict]) -> None:
    phase2 = ROOT / "data/processed/grading_forecast/berry_v3/yolo_phase2"
    train_positive = [line.strip() for line in (phase2 / "train.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
    validation_positive = [line.strip() for line in (phase2 / "validation.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
    split_map = {"NEGATIVE_TRAIN": "train", "NEGATIVE_VALIDATION": "validation"}
    negative_paths: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        if row["split"] not in split_map:
            continue
        split = split_map[row["split"]]
        source = ROOT / row["local_path"]
        destination = YOLO_ROOT / "materialized" / split / "images" / source.name
        copy_derived(source, destination)
        label = YOLO_ROOT / "materialized" / split / "labels" / f"{source.stem}.txt"
        label.parent.mkdir(parents=True, exist_ok=True)
        if not label.exists():
            label.write_text("", encoding="utf-8")
        negative_paths[split].append(destination.resolve().as_posix())
    YOLO_ROOT.mkdir(parents=True, exist_ok=True)
    (YOLO_ROOT / "train.txt").write_text("\n".join(train_positive + sorted(negative_paths["train"])) + "\n", encoding="utf-8")
    (YOLO_ROOT / "validation.txt").write_text("\n".join(validation_positive + sorted(negative_paths["validation"])) + "\n", encoding="utf-8")
    (YOLO_ROOT / "data.yaml").write_text(
        f"path: {YOLO_ROOT.resolve().as_posix()}\ntrain: train.txt\nval: validation.txt\nnames:\n  0: V3 Grade 1\n  1: V3 Grade 2\nnc: 2\n",
        encoding="utf-8",
    )


def validate(rows: list[dict]) -> dict:
    if not rows:
        raise RuntimeError("No usable follow-up negatives")
    hashes = [r["sha256"] for r in rows]
    if len(hashes) != len(set(hashes)):
        raise RuntimeError("Duplicate SHA-256 within follow-up manifest")
    if set(hashes) & forbidden_hashes():
        raise RuntimeError("Follow-up negatives overlap V3 or original Phase 3 by SHA-256")
    group_splits: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        path = ROOT / row["local_path"]
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            raise RuntimeError(f"Manifest/image mismatch: {path}")
        group_splits[row["source_group"]].add(row["split"])
    if any(len(splits) != 1 for splits in group_splits.values()):
        raise RuntimeError("Source-group leakage across partitions")
    split_counts = Counter(r["split"] for r in rows)
    if any(split_counts[name] == 0 for name in ("NEGATIVE_TRAIN", "NEGATIVE_VALIDATION", "NEGATIVE_FINAL_HOLDOUT")):
        raise RuntimeError(f"Missing required partition: {split_counts}")
    category_splits = Counter((r["category"], r["split"]) for r in rows)
    missing = [f"{category}:{split}" for category in {r['category'] for r in rows} for split in split_counts if category_splits[(category, split)] == 0]
    if missing:
        raise RuntimeError(f"Category absent from one or more partitions: {missing}")
    return {"unique_hashes": len(set(hashes)), "source_group_leaks": 0, "manifest_image_consistency": True,
            "all_categories_present_in_all_partitions": True}


def write_summary(rows: list[dict], validation: dict, requested_target: int | None = None) -> None:
    failure_lines = FAILURES.read_text(encoding="utf-8").splitlines() if FAILURES.exists() else []
    failure_records = []
    for line in failure_lines:
        try:
            failure_records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    unique_failures = {}
    for record in failure_records:
        key = record.get("source_page") or f"{record.get('category')}:{record.get('query')}:{record.get('stage')}:{record.get('error')}"
        unique_failures[key] = record
    rejected_errors = ("minimum_dimension", "unsupported_format", "image_exceeds", "duplicate_sha256")
    rejected = sum(any(token in record.get("error", "") for token in rejected_errors) for record in unique_failures.values())
    duplicates = sum("duplicate_sha256" in record.get("error", "") for record in unique_failures.values())
    failed = len(unique_failures) - rejected
    summary = {
        "dataset_version": "berry_v3_phase3_followup_negatives_v1", "seed": SEED,
        "total_requested": max(requested_target or sum(target for target, _ in CATEGORY_PLAN.values()), len(rows)),
        "total_downloaded": len(rows) + rejected, "total_usable": len(rows),
        "total_rejected": rejected, "total_duplicate": duplicates, "total_failed": failed,
        "download_attempt_log_entries": len(failure_lines), "unique_failed_or_rejected_candidates": len(unique_failures),
        "category_counts": dict(sorted(Counter(r["category"] for r in rows).items())),
        "split_counts": dict(sorted(Counter(r["split"] for r in rows).items())),
        "source_counts": dict(sorted(Counter(r["source"] for r in rows).items())),
        "source_group_count": len({r["source_group"] for r in rows}), "hash_duplicate_count": 0,
        "validation": validation, "final_holdout_policy": "sealed until model and threshold freeze",
    }
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, help="Optional smaller total target for an interrupted/slow-network run")
    parser.add_argument("--prepare-only", action="store_true", help="Do not access the network; verify and materialize the cached manifest")
    parser.add_argument("--openverse", action="store_true", help="Fill remaining quotas from Openverse open-license results")
    args = parser.parse_args()
    rows = validate_existing(read_csv(MANIFEST))[0] if args.prepare_only else acquire_openverse(args.target) if args.openverse else acquire(args.target)
    rows = assign_splits(rows)
    write_manifest(rows)
    result = validate(rows)
    prepare_yolo(rows)
    write_summary(rows, result, args.target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

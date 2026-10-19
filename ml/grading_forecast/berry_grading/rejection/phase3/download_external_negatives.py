"""Download and verify the small Wikimedia Commons Phase 3 negative set."""

from __future__ import annotations

import csv
import hashlib
import json
import random
import re
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
OUTPUT_ROOT = ROOT / "data/external/phase3_rejection/non_pepper"
MANIFEST = ROOT / "data/processed/grading_forecast/berry_v3/phase3_negative_manifest.csv"
V3_MANIFEST = ROOT / "data/processed/grading_forecast/berry_v3/v3_image_sample_manifest.csv"
SUMMARY = ROOT / "data/processed/grading_forecast/berry_v3/phase3_negative_dataset_summary.json"
API = "https://commons.wikimedia.org/w/api.php"
SEED = 42
USER_AGENT = "MultimodalPepperAI-Research/Phase3 (educational research; small evaluation set)"

CATEGORY_QUERIES = {
    "people": ["person standing", "people walking", "family outdoors", "crowd street", "portrait man", "portrait woman", "child playing", "worker portrait"],
    "vehicles": ["car road", "bus street", "bicycle", "motorcycle", "truck road", "passenger train", "boat water", "airplane runway"],
    "buildings_indoor": ["house exterior", "office interior", "kitchen room", "bedroom", "school building", "city building", "hallway interior", "living room"],
    "leaves_plants": ["green leaves", "potted plant", "fern plant", "tree leaves", "flower plant", "garden plants", "grass lawn", "cactus plant"],
    "other_crops": ["rice plants", "maize corn field", "potato harvest", "tomatoes harvest", "coffee plant", "tea plantation", "wheat field", "coconut tree"],
    "other_spices_food": ["cinnamon sticks", "star anise spice", "turmeric powder", "cloves spice", "cumin seeds", "plate of food", "bread loaf", "fruit bowl"],
    "soil_ground": ["garden soil", "dry dirt ground", "sand ground", "gravel ground", "mud ground", "forest floor", "clay soil", "stone ground"],
    "containers": ["empty bowl", "plastic bucket", "woven basket", "cardboard box", "cooking pot", "glass jar", "metal tray", "plastic container"],
    "random_objects": ["wooden chair", "wall clock", "book on table", "scissors", "computer keyboard", "shoe object", "umbrella", "toy object"],
    "empty_background": ["empty room", "blank wall", "empty table", "blue sky", "empty road", "plain floor", "white background", "empty field"],
}

CATEGORY_SEARCH = {
    "people": "people outdoors",
    "vehicles": "vehicles transport",
    "buildings_indoor": "building interior",
    "leaves_plants": "plants leaves",
    "other_crops": "agricultural crops",
    "other_spices_food": "food spices",
    "soil_ground": "soil ground",
    "containers": "bowls baskets containers",
    "random_objects": "household objects",
    "empty_background": "empty room landscape",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def request_json(params: dict) -> dict:
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(5):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 4:
                raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("Wikimedia API retry loop ended unexpectedly")


def candidates(query: str) -> list[dict]:
    payload = request_json({
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": f"{query} filetype:bitmap", "gsrnamespace": 6, "gsrlimit": 50,
        "prop": "imageinfo", "iiprop": "url|mime|extmetadata", "iiurlwidth": 800,
    })
    pages = payload.get("query", {}).get("pages", {})
    return sorted(pages.values(), key=lambda page: page.get("index", 999999))


def clean_html(value: str | None) -> str:
    return re.sub(r"<[^>]+>", "", value or "").strip()


def existing_v3_hashes() -> set[str]:
    with V3_MANIFEST.open(newline="", encoding="utf-8-sig") as handle:
        return {row["sha256"].lower() for row in csv.DictReader(handle)}


def validate_existing() -> bool:
    if not MANIFEST.exists():
        return False
    with MANIFEST.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    hashes = set()
    for row in rows:
        path = ROOT / row["local_path"]
        if not path.is_file() or sha256_bytes(path.read_bytes()) != row["sha256"]:
            raise RuntimeError(f"Existing Phase 3 negative manifest failed verification: {path}")
        hashes.add(row["sha256"])
    if len(rows) != 80 or len(hashes) != 80:
        raise RuntimeError("Existing Phase 3 negative set is incomplete or contains duplicate hashes")
    print(f"Verified existing external negative set: {len(rows)} images")
    return True


def main() -> int:
    if validate_existing():
        return 0
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    forbidden_hashes = existing_v3_hashes()
    seen_hashes: set[str] = set()
    used_titles: set[str] = set()
    rows: list[dict] = []

    for category, queries in CATEGORY_QUERIES.items():
        category_dir = OUTPUT_ROOT / category
        category_dir.mkdir(parents=True, exist_ok=True)
        category_rows = []
        combined_query = CATEGORY_SEARCH[category]
        available_pages = candidates(combined_query)
        for query_number in range(1, 9):
            selected = None
            for page in available_pages:
                info_items = page.get("imageinfo") or []
                if not info_items:
                    continue
                info = info_items[0]
                mime, title = info.get("mime", ""), page.get("title", "")
                lowered = title.lower()
                if mime not in {"image/jpeg", "image/png"} or title in used_titles:
                    continue
                if "pepper" in lowered or "capsicum" in lowered:
                    continue
                image_url = info.get("thumburl") or info.get("url")
                if not image_url:
                    continue
                request = urllib.request.Request(image_url, headers={"User-Agent": USER_AGENT})
                try:
                    with urllib.request.urlopen(request, timeout=60) as response:
                        payload = response.read(2_500_000)
                except Exception:
                    continue
                digest = sha256_bytes(payload)
                if digest in seen_hashes or digest in forbidden_hashes:
                    continue
                extension = ".jpg" if mime == "image/jpeg" else ".png"
                image_id = f"{category}_{query_number:03d}"
                path = category_dir / f"{image_id}{extension}"
                path.write_bytes(payload)
                metadata = info.get("extmetadata", {})
                selected = {
                    "image_id": image_id, "category": category, "query": combined_query,
                    "source": "Wikimedia Commons", "source_page_url": info.get("descriptionurl", ""),
                    "download_url": image_url, "commons_title": title,
                    "creator": clean_html(metadata.get("Artist", {}).get("value")),
                    "license_short_name": clean_html(metadata.get("LicenseShortName", {}).get("value")),
                    "license_url": metadata.get("LicenseUrl", {}).get("value", ""),
                    "attribution": clean_html(metadata.get("Credit", {}).get("value")),
                    "local_path": path.relative_to(ROOT).as_posix(), "sha256": digest, "bytes": len(payload),
                }
                used_titles.add(title)
                seen_hashes.add(digest)
                break
            if selected is None:
                raise RuntimeError(f"Could not find eight unique JPEG/PNG images for {category}")
            category_rows.append(selected)
        time.sleep(2.0)

        rng = random.Random(f"{SEED}:{category}")
        rng.shuffle(category_rows)
        for index, row in enumerate(category_rows):
            row["phase3_partition"] = "CALIBRATION" if index < 4 else "EVALUATION"
        rows.extend(category_rows)

    fields = ["image_id", "category", "phase3_partition", "query", "source", "source_page_url", "download_url", "commons_title", "creator", "license_short_name", "license_url", "attribution", "local_path", "sha256", "bytes"]
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: row["image_id"]))

    summary = {
        "source": "Wikimedia Commons", "thumbnail_max_width": 800, "seed": SEED,
        "images": len(rows),
        "categories": {category: sum(r["category"] == category for r in rows) for category in CATEGORY_QUERIES},
        "partitions": {name: sum(r["phase3_partition"] == name for r in rows) for name in ("CALIBRATION", "EVALUATION")},
        "download_bytes": sum(int(r["bytes"]) for r in rows), "unique_hashes": len(seen_hashes),
        "v3_hash_overlap": len(seen_hashes & forbidden_hashes),
    }
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

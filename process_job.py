#!/usr/bin/env python3
"""
process_job.py - Headless Reel Generation & Instagram Publishing Runner
Designed to run in GitHub Actions (or locally) triggered by WhatsApp / Cloudflare Worker.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import random
import re
import sys
import uuid
from pathlib import Path
from typing import Any

import cloudinary
import cloudinary.uploader
import requests
from dotenv import load_dotenv

from instagram_publisher import publish_reel
from reel_generator import THEMES, generate_all, generate_reel

load_dotenv(override=True)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("process_job")

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("generated")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v27.0")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
WHATSAPP_AUTO_PUBLISH = os.getenv("WHATSAPP_AUTO_PUBLISH", "true").strip().lower() in {
    "1", "true", "yes", "on"
}

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)


def _normalise_price(amount: str) -> str:
    amount = amount.replace(",", "").strip()
    try:
        numeric = float(amount)
        if numeric.is_integer():
            return f"₹{int(numeric):,}"
        return f"₹{numeric:,.2f}"
    except ValueError:
        return f"₹{amount}"


def parse_product_caption(caption: str) -> tuple[str | None, str, str]:
    """Parse product name, description and price from WhatsApp message caption."""
    lines = [line.strip() for line in caption.replace("\r", "").split("\n") if line.strip()]
    product_name: str | None = None
    description_lines: list[str] = []
    price = ""
    description_mode = False

    price_patterns = [
        re.compile(r"\bprice\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)", re.I),
        re.compile(r"@\s*(?:₹|rs\.?|inr)?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)", re.I),
        re.compile(r"₹\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)", re.I),
        re.compile(r"\b([0-9][0-9,]*(?:\.[0-9]{1,2})?)\s*(?:rs\.?|inr|/-)", re.I),
    ]

    for line in lines:
        product_match = re.match(r"^(?:product(?:\s*name)?|item|name)\s*:\s*(.+)$", line, re.I)
        if product_match:
            product_name = product_match.group(1).strip()
            description_mode = False
            continue

        description_match = re.match(r"^(?:description|details)\s*:\s*(.*)$", line, re.I)
        if description_match:
            description_mode = True
            value = description_match.group(1).strip()
            if value:
                description_lines.append(value)
            continue

        found_price = None
        bare_price_only = False
        for pattern in price_patterns:
            match = pattern.search(line)
            if match:
                found_price = match.group(1)
                break
        if found_price is None and product_name:
            bare_amount = re.fullmatch(r"\s*(?:₹\s*)?([0-9][0-9,]*(?:\.[0-9]{1,2})?)\s*", line)
            if bare_amount:
                found_price = bare_amount.group(1)
                bare_price_only = True
        if found_price is not None:
            price = _normalise_price(found_price)
            if bare_price_only or re.match(r"(?i)^\s*price\s*[:\-]?", line):
                continue
            cleaned = re.sub(r"(?i)\bprice\s*[:\-]?", "", line)
            for pattern in price_patterns:
                cleaned = pattern.sub("", cleaned)
            cleaned = cleaned.strip(" \t-:@₹")
            cleaned = re.sub(r"(?i)^\s*(?:rs\.?|inr)\s*", "", cleaned).strip()
            if cleaned:
                if product_name is None and not description_mode:
                    product_name = cleaned
                else:
                    description_lines.append(cleaned)
            continue

        if description_mode:
            description_lines.append(line)
        elif product_name is None:
            product_name = line
        else:
            description_lines.append(line)

    if product_name:
        product_name = product_name.strip()
        if re.fullmatch(r"[₹\s]*[0-9][0-9,.]*", product_name):
            product_name = None

    description = "\n".join(description_lines).strip()
    return product_name, description, price


def build_instagram_caption(product_name: str, price: str, description: str) -> str:
    caption_parts = [product_name]
    if description.strip():
        caption_parts.append(description.strip())
    if price.strip():
        caption_parts.append(f"Price: {price.strip()}")
    caption_parts.extend(
        [
            "DM us to order 💌",
            "#SRRBazaar #Shopping #IndianFashion #OnlineShopping",
        ]
    )
    return "\n\n".join(caption_parts)[:2200]


def download_whatsapp_media(media_id: str, destination_dir: Path) -> Path:
    """Download image from Meta Graph API using WhatsApp media_id."""
    if not WHATSAPP_ACCESS_TOKEN:
        raise ValueError("WHATSAPP_ACCESS_TOKEN is required to download WhatsApp media")

    media_endpoint = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}

    logger.info("Querying Meta media endpoint: %s", media_endpoint)
    res = requests.get(media_endpoint, headers=headers, timeout=30)
    if not res.ok:
        raise RuntimeError(f"Media lookup failed ({res.status_code}): {res.text}")

    data = res.json()
    media_url = data.get("url")
    if not media_url:
        raise RuntimeError("No media URL in Meta API response")

    content_type = str(data.get("mime_type") or "").split(";")[0].lower()
    extensions = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    ext = extensions.get(content_type, ".jpg")

    logger.info("Downloading image file from: %s", media_url)
    dl = requests.get(media_url, headers=headers, timeout=60)
    if not dl.ok:
        raise RuntimeError(f"Media download failed ({dl.status_code}): {dl.text}")

    out_path = destination_dir / f"wa_{media_id}{ext}"
    out_path.write_bytes(dl.content)
    logger.info("Saved WhatsApp image to %s (%d bytes)", out_path, len(dl.content))
    return out_path


def upload_to_cloudinary(video_path: Path) -> str:
    logger.info("Uploading %s to Cloudinary...", video_path.name)
    result = cloudinary.uploader.upload(
        str(video_path),
        resource_type="video",
        folder="product_reels",
    )
    secure_url = result.get("secure_url")
    if not secure_url:
        raise RuntimeError(f"Cloudinary upload failed: {result}")
    logger.info("Cloudinary URL: %s", secure_url)
    return secure_url


def send_whatsapp_reply(to: str, message: str) -> None:
    """Send confirmation notification to sender via WhatsApp Cloud API."""
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID or not to:
        return
    url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to.strip().lstrip("+"),
        "type": "text",
        "text": {"body": message},
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        logger.info("WhatsApp notification sent (status %d)", resp.status_code)
    except Exception as exc:
        logger.warning("Could not send WhatsApp notification: %s", exc)


def sync_product_to_website_catalogue(
    image_path: Path,
    product_name: str,
    price_str: str,
    description: str,
    job_id: str,
) -> None:
    """Auto-add product to docs/products.json and docs/images/catalog/ for live website."""
    try:
        docs_dir = Path("docs")
        if not docs_dir.exists():
            return

        catalog_img_dir = docs_dir / "images" / "catalog"
        catalog_img_dir.mkdir(parents=True, exist_ok=True)

        target_img_name = f"{job_id}.jpg"
        target_img_path = catalog_img_dir / target_img_name

        if image_path.exists():
            target_img_path.write_bytes(image_path.read_bytes())

        # Extract numeric price
        numeric_match = re.search(r"([0-9][0-9,]*)", price_str.replace(",", ""))
        numeric_price = int(numeric_match.group(1)) if numeric_match else 999
        original_price = int(numeric_price * 1.5)

        # Detect category based on product title/description
        text_lower = f"{product_name} {description}".lower()
        category = "necklace"
        if any(w in text_lower for w in ["bead", "mangalsutra", "black", "chain"]):
            category = "mangalsutra"
        elif any(w in text_lower for w in ["earring", "stud", "jhumka", "bangle", "bracelet"]):
            category = "earrings"
        elif any(w in text_lower for w in ["tray", "swan", "decor", "pooja", "gift"]):
            category = "decor"

        products_json_path = docs_dir / "products.json"
        products: list[dict[str, Any]] = []
        if products_json_path.exists():
            try:
                products = json.loads(products_json_path.read_text(encoding="utf-8"))
            except Exception:
                products = []

        new_entry = {
            "id": int(uuid.uuid4().int % 1000000000),
            "title": product_name,
            "category": category,
            "price": numeric_price,
            "originalPrice": original_price,
            "tag": "New Arrival",
            "image": f"images/catalog/{target_img_name}",
            "description": description or f"Exclusive {product_name} with premium finish. Free express shipping across India.",
            "inStock": True,
            "rating": 5.0,
            "reviewsCount": 1,
        }

        # Prepend to catalogue so new arrivals appear first
        products.insert(0, new_entry)
        products_json_path.write_text(json.dumps(products, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Auto-synced new product to website catalogue: '%s' (₹%d) -> %s", product_name, numeric_price, target_img_name)
    except Exception as e:
        logger.warning("Could not auto-sync product to website catalogue: %s", e)


def main() -> int:
    parser = argparse.ArgumentParser(description="Process WhatsApp submission and publish Instagram Reel")
    parser.add_argument("--media-id", help="WhatsApp media ID to download")
    parser.add_argument("--image-path", help="Local image path")
    parser.add_argument("--image-url", help="Direct public image URL")
    parser.add_argument("--caption", default="", help="Raw product caption")
    parser.add_argument("--sender", default="", help="Sender phone number")
    parser.add_argument("--message-id", default="", help="WhatsApp message ID")
    parser.add_argument("--theme", default="random", help="Theme to select or 'random' (generates all 4)")
    parser.add_argument("--auto-publish", choices=["true", "false"], default=None, help="Auto publish to Instagram")

    args = parser.parse_args()

    # Parse auto_publish setting
    auto_publish = WHATSAPP_AUTO_PUBLISH if args.auto_publish is None else (args.auto_publish == "true")

    job_id = uuid.uuid4().hex[:12]
    job_output_dir = OUTPUT_DIR / job_id
    job_output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Resolve product image
    image_file: Path | None = None
    if args.media_id:
        image_file = download_whatsapp_media(args.media_id, UPLOAD_DIR)
    elif args.image_url:
        logger.info("Downloading image from URL: %s", args.image_url)
        resp = requests.get(args.image_url, timeout=30)
        resp.raise_for_status()
        image_file = UPLOAD_DIR / f"url_{job_id}.jpg"
        image_file.write_bytes(resp.content)
    elif args.image_path:
        image_file = Path(args.image_path)
    else:
        # Default fallback test image if uploads/necklace.jpg exists
        test_img = Path("uploads/necklace.jpg")
        if test_img.exists():
            image_file = test_img
            logger.info("No image specified; using default fallback: %s", test_img)
        else:
            logger.error("No input image specified (provide --media-id, --image-url, or --image-path)")
            return 1

    if not image_file or not image_file.exists():
        logger.error("Image file does not exist: %s", image_file)
        return 1

    # 2. Parse product details
    caption_text = args.caption.strip()
    product_name, description, price = parse_product_caption(caption_text)
    if not product_name:
        product_name = "Exclusive Collection"
        logger.warning("No product name detected in caption; using default: %s", product_name)
    if not price:
        price = "Special Offer"

    logger.info("Parsed Product: '%s' | Price: '%s'", product_name, price)

    # 3. Generate all 4 Reel themes
    logger.info("Generating all 4 Reel themes in %s...", job_output_dir)
    generated_videos = generate_all(
        image_path=image_file,
        product_name=product_name,
        price=price,
        output_dir=job_output_dir,
    )

    if not generated_videos:
        logger.error("Failed to generate any Reels")
        return 1

    # 4. Choose one video
    if args.theme in THEMES:
        selected_video = job_output_dir / f"{args.theme}.mp4"
        if not selected_video.exists():
            selected_video = Path(random.choice(generated_videos))
    else:
        selected_video = Path(random.choice(generated_videos))

    logger.info("Selected theme for publishing: %s (%s)", selected_video.stem, selected_video)

    # Copy / save a pointer or symlink for GitHub Actions output
    latest_reel = OUTPUT_DIR / "latest_reel.mp4"
    latest_reel.write_bytes(selected_video.read_bytes())

    # 5. Publish to Instagram (if enabled)
    if auto_publish:
        logger.info("Auto-publish is enabled. Uploading to Cloudinary...")
        video_url = upload_to_cloudinary(selected_video)

        ig_caption = build_instagram_caption(product_name, price, description)
        logger.info("Publishing to Instagram with caption:\n%s", ig_caption)

        publish_res = publish_reel(video_url, ig_caption)
        media_id = publish_res.get("media_id", "")
        logger.info("SUCCESS: Instagram Reel published! Media ID: %s", media_id)

        # Notify sender on WhatsApp
        if args.sender:
            notification_text = (
                f"🎉 Your Reel for '{product_name}' has been created and published to Instagram!\n\n"
                f"Theme: {selected_video.stem}\n"
                f"Price: {price}\n"
                f"Status: Live on Instagram & Website Catalogue"
            )
            send_whatsapp_reply(args.sender, notification_text)

        # Auto-sync to website catalogue
        sync_product_to_website_catalogue(
            image_path=image_file,
            product_name=product_name,
            price_str=price,
            description=description,
            job_id=job_id,
        )
    else:
        logger.info("WHATSAPP_AUTO_PUBLISH=false. Reels generated and stored in %s without publishing.", job_output_dir)
        # Even if not auto-published, sync product to catalogue
        sync_product_to_website_catalogue(
            image_path=image_file,
            product_name=product_name,
            price_str=price,
            description=description,
            job_id=job_id,
        )

    print(json.dumps({
        "status": "success",
        "job_id": job_id,
        "product_name": product_name,
        "price": price,
        "selected_theme": selected_video.stem,
        "selected_reel": str(selected_video),
        "all_reels": [str(p) for p in generated_videos],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

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
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import cloudinary
import cloudinary.uploader
import requests
from dotenv import load_dotenv

from instagram_publisher import publish_reel
from youtube_publisher import publish_youtube_short
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


def _clean_typography(text: str) -> str:
    """Strip WhatsApp markdown and unsupported emojis that render as missing glyph boxes."""
    cleaned = re.sub(r"[*_~`]", "", text)
    emoji_pattern = re.compile(
        "[\U00010000-\U0010ffff]"
        "|[\u2600-\u27bf]"
        "|[\u2300-\u23ff]"
        "|[\ufe00-\ufe0f]",
        flags=re.UNICODE,
    )
    cleaned = emoji_pattern.sub("", cleaned)
    return " ".join(cleaned.split()).strip()


EXPLICIT_PRICE_PATTERNS = [
    # 'offer price only 499', 'price : 1300', 'price 799'
    re.compile(r"\b(?:offer\s*price|price|mrp)\s*[:\-]?\s*(?:only|just)?\s*(?:₹|rs\.?|inr)?\s*([0-9][0-9,]*)", re.I),
    # '1 set 499', 'single 550'
    re.compile(r"\b(?:1\s*set|single)\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*([0-9][0-9,]*)", re.I),
    # '1300 rs', '1300rs', '1555/-rs', '799/-'
    re.compile(r"\b([0-9][0-9,]*)\s*(?:/-\s*rs\.?|rs\.?|inr|/-)\b", re.I),
    # '₹ 1300', 'rs. 1300', 'rs 1300'
    re.compile(r"(?:₹|rs\.?|inr)\s*[:\-]?\s*([0-9][0-9,]*)", re.I),
    # 'only 1999', 'just 499'
    re.compile(r"\b(?:only|just)\s*(?:₹|rs\.?|inr)?\s*([0-9][0-9,]*)", re.I),
    # '450 fs', '550 free shipping', '999/+ freeshipping'
    re.compile(r"\b([0-9][0-9,]*)\s*(?:/-\s*)?(?:\+\s*)?(?:free\s*shipping|freeshipping|free\s*delivery|ship\s*free|fs)\b", re.I),
    # '@ 1199'
    re.compile(r"@\s*(?:₹|rs\.?|inr)?\s*([0-9][0-9,]*)", re.I),
]


def parse_product_caption(caption: str) -> tuple[str, str, str]:
    """Parse product name, description and price accurately from WhatsApp message caption.
    Guarantees a high-quality product name & description even if caption has only price or is blank.
    """
    raw_lines = [line.strip() for line in caption.replace("\r", "").split("\n") if line.strip()]
    lines = [_clean_typography(line) for line in raw_lines if _clean_typography(line)]
    full_text = " \n ".join(lines) if lines else ""

    # 1. EXTRACT PRICE WITH STRICT EXPLICIT PRIORITY
    chosen_price = None

    if full_text:
        # Priority A: Check for explicit multi-tier or single item price (e.g. '1 set 499')
        single_match = re.search(r"\b(?:1\s*set|single)\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*([0-9][0-9,]*)", full_text, re.I)
        if single_match:
            val = int(single_match.group(1).replace(",", ""))
            if 50 <= val <= 200000:
                chosen_price = val

        # Priority B: Check explicit price indicators
        if not chosen_price:
            for pattern in EXPLICIT_PRICE_PATTERNS:
                matches = list(pattern.finditer(full_text))
                if matches:
                    for m in matches:
                        val = int(m.group(1).replace(",", ""))
                        if 50 <= val <= 200000:
                            chosen_price = val
                            break
                if chosen_price:
                    break

        # Priority C: Standalone number lines (e.g. line is purely '850' or '2888')
        if not chosen_price:
            for l in lines:
                if re.fullmatch(r"[₹\s]*[0-9]{3,5}[/\-\s]*\.?", l):
                    num_match = re.search(r"\d+", l)
                    if num_match:
                        val = int(num_match.group(0))
                        if 50 <= val <= 200000:
                            chosen_price = val
                            break

    # 2. EXTRACT PRODUCT NAME & DESCRIPTION
    product_name: str | None = None
    description_lines: list[str] = []

    for l in lines:
        name_match = re.match(r"^(?:product(?:\s*name)?|item|name)\s*[:\-]\s*(.+)$", l, re.I)
        if name_match:
            product_name = name_match.group(1).strip()
            continue

        desc_match = re.match(r"^(?:description|details)\s*[:\-]\s*(.*)$", l, re.I)
        if desc_match:
            if desc_match.group(1).strip():
                description_lines.append(desc_match.group(1).strip())
            continue

        # Skip lines that are purely the price (e.g. '1300 rs', '₹1300', '2888')
        if chosen_price and re.fullmatch(
            rf"[₹\s]*(?:only|just|price|offer\s*price|mrp)?\s*[:\-]?(?:rs\.?|inr|₹)?\s*{chosen_price}\s*(?:/-\s*rs\.?|rs\.?|inr|/-|free\s*shipping|freeshipping|fs)?\.?",
            l,
            re.I,
        ):
            continue

        if re.fullmatch(r"[₹\s]*[0-9]{3,5}[/\-\s]*\.?", l):
            continue

        # First meaningful descriptive line becomes product name
        if product_name is None:
            product_name = l
        else:
            description_lines.append(l)

    # Polish Product Name
    if product_name:
        if re.match(r"^\d+\s*(?:pieces?|pcs?|bowls?|diyas?)\s*(?:each)?$", product_name, re.I) and description_lines:
            product_name = f"{product_name} - {description_lines[0]}"
        elif product_name.strip().lower().endswith((" with", " for", " and", " of", " in", "&")) and description_lines:
            product_name = f"{product_name} {description_lines[0]}"

        if chosen_price:
            product_name = re.sub(
                rf"(?i)\s*[:\-]?\s*(?:only|just)?\s*(?:₹|rs\.?|inr)?\s*{chosen_price}\s*(?:/-\s*rs\.?|rs\.?|inr|/-|free\s*shipping|freeshipping|fs)?\.?",
                "",
                product_name,
            ).strip()

        product_name = product_name.strip(" ,.-–—\t\r\n")

    # 3. STABLE FALLBACK WHEN NO PRODUCT NAME IS PROVIDED IN CAPTION
    if not product_name:
        if chosen_price:
            if chosen_price >= 1200:
                product_name = "Premium Bridal Pure Jadau Kundan Collection"
            elif chosen_price >= 750:
                product_name = "Festive Handcrafted Traditional Collection"
            elif chosen_price >= 400:
                product_name = "Handcrafted Designer Jewellery Collection"
            else:
                product_name = "SRR Bazaar Curated Collection"
        else:
            product_name = "SRR Bazaar Curated Collection"

    description = "\n".join(description_lines).strip()
    if not description:
        description = (
            f"Exclusive {product_name} by SRR Bazaar. "
            "Premium artisanal finish, non-allergic skin-safe materials, express pan-India dispatch and Cash on Delivery available. "
            "Direct WhatsApp order assist: +91 8185012453."
        )

    price_str = f"₹{chosen_price:,}" if chosen_price else "Special Offer"
    return product_name, description, price_str


def build_instagram_caption(product_name: str, price: str, description: str) -> str:
    caption_parts = []
    clean_name = product_name.strip() if product_name else "Exclusive Collection"
    caption_parts.append(f"✨ {clean_name} ✨")

    if description.strip():
        caption_parts.append(description.strip())

    price_str = price.strip() if price else ""
    if price_str:
        if not price_str.startswith("₹"):
            price_str = f"₹{price_str}"
        caption_parts.append(
            f"🏷️ Launch Price: {price_str} ONLY\n"
            "🚚 FREE Express Shipping Pan-India\n"
            "📦 Cash on Delivery (COD) Available\n"
            "💯 Premium Quality Guaranteed"
        )
    else:
        caption_parts.append(
            "🚚 FREE Express Shipping Pan-India\n"
            "📦 Cash on Delivery (COD) Available\n"
            "💯 Premium Quality Guaranteed"
        )

    caption_parts.append(
        "👉 HOW TO ORDER:\n"
        "1️⃣ Tap the link in bio (@sujatha60861) or visit https://srrbazaar.com\n"
        "2️⃣ WhatsApp / Call to order directly:\n"
        "   📲 +91 9948633303\n"
        "   📲 +91 8185012453\n"
        "3️⃣ Or comment \"PRICE\" / \"BUY\" below and we'll DM you the direct link!"
    )

    caption_parts.append(
        "#SRRBazaar #SujathaCollections #Sarees #SareeLove #KhadiCotton #SilkSarees "
        "#FashionJewellery #KundanJewellery #BridalJewellery #Kurtis #HomeDecor "
        "#IndianFashion #OnlineShoppingIndia #PanIndiaShipping #COD #HyderabadShopping "
        "#BestDeals #DesiFashion #FestiveWear"
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
        "video/mp4": ".mp4",
        "video/quicktime": ".mov",
        "video/3gpp": ".3gp",
        "video/webm": ".webm",
        "video/x-msvideo": ".avi",
    }
    ext = extensions.get(content_type)
    if not ext:
        ext = ".mp4" if content_type.startswith("video/") else ".jpg"

    logger.info("Downloading media file (%s) from: %s", content_type, media_url)
    dl = requests.get(media_url, headers=headers, timeout=60)
    if not dl.ok:
        raise RuntimeError(f"Media download failed ({dl.status_code}): {dl.text}")

    out_path = destination_dir / f"wa_{media_id}{ext}"
    out_path.write_bytes(dl.content)
    logger.info("Saved WhatsApp media to %s (%d bytes)", out_path, len(dl.content))
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
        if resp.status_code == 200:
            logger.info("WhatsApp notification sent successfully to %s", to)
        else:
            logger.warning("WhatsApp notification failed (%d): %s", resp.status_code, resp.text)
    except Exception as exc:
        logger.warning("Could not send WhatsApp notification: %s", exc)


def sync_product_to_website_catalogue(
    image_path: Path,
    product_name: str,
    price_str: str,
    description: str,
    job_id: str,
    video_path: Path | None = None,
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

        # Ensure target_img_path receives a real JPEG image, NEVER an MP4 video file
        is_video_input = False
        if image_path.exists():
            header = b""
            with open(image_path, "rb") as f_chk:
                header = f_chk.read(16)
            if b"ftyp" in header or b"moov" in header or image_path.suffix.lower() in {".mp4", ".mov", ".3gp", ".webm", ".avi"}:
                is_video_input = True

        if is_video_input:
            vid_src = str(video_path if (video_path and Path(video_path).exists()) else image_path)
            extracted = False
            # 1. Grab 1st frame (no -ss seek, 100% reliable)
            cmd_frame0 = [
                "ffmpeg", "-y",
                "-i", vid_src,
                "-vframes", "1",
                "-q:v", "2",
                str(target_img_path)
            ]
            try:
                res = subprocess.run(cmd_frame0, capture_output=True)
                if res.returncode == 0 and target_img_path.exists() and target_img_path.stat().st_size > 1000:
                    with open(target_img_path, "rb") as f_res:
                        magic = f_res.read(4)
                    if magic.startswith(b"\xff\xd8"):
                        extracted = True
                        logger.info("Auto-extracted 1st frame cover from video: %s", target_img_path)
            except Exception as e:
                logger.warning("Frame 0 extraction attempt failed: %s", e)

            if not extracted:
                for seek_t in ["00:00:00.100", "00:00:00.500", "00:00:01"]:
                    cmd = [
                        "ffmpeg", "-y",
                        "-ss", seek_t,
                        "-i", vid_src,
                        "-vframes", "1",
                        "-q:v", "2",
                        str(target_img_path)
                    ]
                    try:
                        res = subprocess.run(cmd, capture_output=True)
                        if res.returncode == 0 and target_img_path.exists() and target_img_path.stat().st_size > 1000:
                            with open(target_img_path, "rb") as f_res:
                                if f_res.read(4).startswith(b"\xff\xd8"):
                                    extracted = True
                                    logger.info("Auto-extracted JPEG cover from video at %s: %s", seek_t, target_img_path)
                                    break
                    except Exception:
                        pass
            if not extracted:
                fallback_img = catalog_img_dir / "88846458a4a544eda9c03477c177b77a.jpg"
                if fallback_img.exists():
                    target_img_path.write_bytes(fallback_img.read_bytes())
                    logger.warning("Video thumbnail extraction failed; fell back to default catalog image: %s", fallback_img)
        elif image_path.exists():
            target_img_path.write_bytes(image_path.read_bytes())

        # Extract numeric price
        numeric_match = re.search(r"([0-9][0-9,]*)", price_str.replace(",", ""))
        numeric_price = int(numeric_match.group(1)) if numeric_match else 999
        original_price = int(numeric_price * 1.5)

        # Detect category based on product title/description with STRICT word boundaries
        text_lower = f"{product_name} {description}".lower()
        words = set(re.findall(r'\b[a-z0-9]+\b', text_lower))
        
        def has_phrase(phrase: str) -> bool:
            return bool(re.search(r'\b' + re.escape(phrase.lower()) + r'\b', text_lower))
            
        def has_word(w: str) -> bool:
            return w.lower() in words

        # 1. Cleaning & Hygiene
        if any(has_phrase(x) for x in ["bleaching powder", "floor cleaner", "toilet cleaner", "phenyl", "stain remover", "disinfectant"]) or any(has_word(x) for x in ["bleach", "bleaching", "acid", "phenyl", "phenyls", "harpic", "lizol", "detergent", "disinfectant"]):
            category = "cleaning"
        # 2. Electricals & Lighting
        elif any(has_word(x) for x in ["led", "bulb", "bulbs", "tubelight", "batten", "lighting", "electrical", "torch", "holder", "socket", "switch"]):
            category = "electrical"
        # 3. Disposables & Catering
        elif any(has_phrase(x) for x in ["buffet plate", "buffet plates", "leaf plate", "leaf plates", "paper cup", "paper cups", "biodegradable plate", "meal box", "tiffin box", "silver foil"]) or (has_word("disposables") and not has_word("necklace")):
            category = "disposables"
        # 4. Sarees & Handloom
        elif any(has_phrase(x) for x in ["khadhi cotton", "khadi cotton", "pure saree", "silk saree"]) or any(has_word(x) for x in ["saree", "sarees", "sari"]):
            category = "saree"
        # 5. Pooja Decor & Trays
        elif any(has_phrase(x) for x in ["swan tray", "diya stand", "lotus flower", "pooja plate", "brass bowl", "swan organizer"]) or any(has_word(x) for x in ["diya", "diyas", "deepam", "deepalu", "kondalu", "nomu", "nomulu", "kalash", "thali"]):
            category = "decor"
        # 6. Pooja Samagri & Essentials
        elif any(has_word(x) for x in ["wick", "wicks", "batti", "camphor", "karpooram", "kapoor", "dhoop", "agarbatti", "incense", "sambrani", "kumkum", "pasupu", "gandham"]):
            category = "samagri"
        # 7. Black Beads & Mangalsutras
        elif any(has_phrase(x) for x in ["black beads", "nallapusalu", "tulip mala", "tulips mala"]) or any(has_word(x) for x in ["mangalsutra", "nallapusalu"]):
            category = "mangalsutra"
        # 8. Pure Earrings & Bangles (when not a full necklace/bridal set)
        elif not any(has_word(x) for x in ["necklace", "haram", "choker", "haar", "kundan", "jadau", "bridal"]) and any(has_word(x) for x in ["earring", "earrings", "jhumka", "jhumkas", "stud", "studs", "bangle", "bangles", "kada"]):
            category = "earrings"
        # 9. Dry Fruits & Nuts
        elif any(has_word(x) for x in ["almond", "badam", "cashew", "kaju", "pista", "raisin", "kishmish", "walnut", "dryfruit", "dryfruits", "dates", "khajoor", "anjeer"]):
            category = "dryfruits"
        # 10. Snacks & Namkeen
        elif any(has_word(x) for x in ["chips", "biscuit", "biscuits", "namkeen", "mixture", "cookie", "cookies", "murukku", "sev", "bhujia"]):
            category = "snacks"
        # 11. Groceries & Daily Staples (STRICT WHOLE WORD ONLY)
        elif any(has_word(x) for x in ["grocery", "groceries", "rice", "dal", "flour", "atta", "wheat", "ghee", "masala", "spices", "chilli", "mirchi", "turmeric", "salt", "sugar", "jaggery", "bellam", "rava", "suji", "maida", "besan", "pulses", "lentils", "tamarind"]):
            category = "groceries"
        else:
            category = "necklace"

        new_id = int(uuid.uuid4().int % 1000000000)

        # Process and link matching video reel if available
        linked_video_rel = None
        if video_path and Path(video_path).exists():
            try:
                docs_video_dir = docs_dir / "videos"
                docs_video_dir.mkdir(parents=True, exist_ok=True)
                dest_video_name = f"reel_{new_id}.mp4"
                dest_video_path = docs_video_dir / dest_video_name
                
                cmd = [
                    "ffmpeg", "-y", "-i", str(video_path),
                    "-vf", "scale=540:-2",
                    "-c:v", "libx264", "-crf", "26", "-preset", "fast",
                    "-c:a", "aac", "-b:a", "96k",
                    "-movflags", "+faststart",
                    str(dest_video_path)
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if dest_video_path.exists():
                    linked_video_rel = f"videos/{dest_video_name}"
                    logger.info("Auto-compressed & linked matching reel to product %d: %s", new_id, linked_video_rel)
            except Exception as ve:
                logger.warning("Could not link video reel to new product: %s", ve)

        products_json_path = docs_dir / "products.json"
        products: list[dict[str, Any]] = []
        if products_json_path.exists():
            try:
                products = json.loads(products_json_path.read_text(encoding="utf-8"))
            except Exception:
                products = []

        new_entry = {
            "id": new_id,
            "title": product_name,
            "category": category,
            "price": numeric_price,
            "originalPrice": original_price,
            "tag": "New Arrival",
            "image": f"images/catalog/{target_img_name}",
            "video": linked_video_rel,
            "description": description or f"Exclusive {product_name} with premium finish. Free express shipping across India.",
            "inStock": True,
            "rating": 5.0,
            "reviewsCount": 1,
        }

        # Prepend to catalogue so new arrivals appear first
        products.insert(0, new_entry)
        products_json_path.write_text(json.dumps(products, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Auto-synced new product to website catalogue: '%s' (₹%d) -> %s (video: %s)", product_name, numeric_price, target_img_name, linked_video_rel)

        # Also sync docs/index.html DEFAULT_PRODUCTS fallback
        try:
            index_path = docs_dir / "index.html"
            if index_path.exists():
                idx_html = index_path.read_text(encoding="utf-8")
                m = re.search(r'const DEFAULT_PRODUCTS\s*=\s*(\[.*?\]);', idx_html, re.DOTALL)
                if m:
                    idx_prods = json.loads(m.group(1))
                    idx_prods.insert(0, new_entry)
                    new_idx_json = json.dumps(idx_prods, indent=2, ensure_ascii=False)
                    updated_idx_html = idx_html[:m.start(1)] + new_idx_json + idx_html[m.end(1):]
                    index_path.write_text(updated_idx_html, encoding="utf-8")
                    logger.info("Auto-updated DEFAULT_PRODUCTS fallback in docs/index.html")
        except Exception as idx_err:
            logger.warning("Could not update docs/index.html fallback: %s", idx_err)

        # Generate individual product share/SEO page
        try:
            from generate_product_pages import generate_all_product_pages
            generate_all_product_pages()
        except Exception as gen_err:
            logger.warning("Could not generate individual product page: %s", gen_err)
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

    # 3. Process Video or Generate all 4 Reel themes from Image
    header = b""
    if image_file.exists():
        with open(image_file, "rb") as f_chk:
            header = f_chk.read(16)
    is_video = (image_file.suffix.lower() in {".mp4", ".mov", ".3gp", ".webm", ".avi"}) or (b"ftyp" in header or b"moov" in header)
    catalog_cover_image = image_file

    if is_video:
        logger.info("Input media is a video (%s). Extracting cover thumbnail...", image_file.name)
        thumbnail_file = job_output_dir / f"{image_file.stem}_thumb.jpg"
        thumb_ok = False
        # 1. Grab 1st frame (no -ss seek, 100% reliable)
        cmd_frame0 = [
            "ffmpeg", "-y",
            "-i", str(image_file),
            "-vframes", "1",
            "-q:v", "2",
            str(thumbnail_file)
        ]
        try:
            subprocess.run(cmd_frame0, check=True, capture_output=True)
            if thumbnail_file.exists() and thumbnail_file.stat().st_size > 1000:
                with open(thumbnail_file, "rb") as f_res:
                    if f_res.read(4).startswith(b"\xff\xd8"):
                        catalog_cover_image = thumbnail_file
                        thumb_ok = True
                        logger.info("Extracted 1st frame cover thumbnail: %s (%d bytes)", thumbnail_file, thumbnail_file.stat().st_size)
        except Exception as e:
            logger.warning("Frame 0 thumbnail extraction attempt failed: %s", e)

        if not thumb_ok:
            for seek_t in ["00:00:00.100", "00:00:00.500", "00:00:01"]:
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", seek_t,
                    "-i", str(image_file),
                    "-vframes", "1",
                    "-q:v", "2",
                    str(thumbnail_file)
                ]
                try:
                    subprocess.run(cmd, check=True, capture_output=True)
                    if thumbnail_file.exists() and thumbnail_file.stat().st_size > 1000:
                        with open(thumbnail_file, "rb") as f_res:
                            if f_res.read(4).startswith(b"\xff\xd8"):
                                catalog_cover_image = thumbnail_file
                                thumb_ok = True
                                logger.info("Extracted cover thumbnail at %s: %s (%d bytes)", seek_t, thumbnail_file, thumbnail_file.stat().st_size)
                                break
                except Exception as e:
                    logger.warning("Could not extract thumbnail frame at %s via ffmpeg: %s", seek_t, e)

        if not thumb_ok:
            fallback_img = Path("docs/images/catalog/88846458a4a544eda9c03477c177b77a.jpg")
            if fallback_img.exists():
                catalog_cover_image = fallback_img
                logger.warning("Fell back to default catalog cover: %s", fallback_img)

        selected_video = image_file
        generated_videos = [selected_video]
    else:
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

        # Publish to YouTube Shorts (if configured)
        yt_title = f"{product_name} {price} | SRR Bazaar #Shorts"
        try:
            yt_res = publish_youtube_short(
                video_source=str(selected_video),
                title=yt_title,
                description=ig_caption,
            )
            if yt_res.get("status") == "published":
                logger.info("SUCCESS: YouTube Short published! URL: %s", yt_res.get("url"))
        except Exception as yt_err:
            logger.warning("YouTube Shorts publishing skipped/failed: %s", yt_err)

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
            image_path=catalog_cover_image,
            product_name=product_name,
            price_str=price,
            description=description,
            job_id=job_id,
            video_path=selected_video,
        )
    else:
        logger.info("WHATSAPP_AUTO_PUBLISH=false. Reels generated and stored in %s without publishing.", job_output_dir)
        # Even if not auto-published, sync product to catalogue
        sync_product_to_website_catalogue(
            image_path=catalog_cover_image,
            product_name=product_name,
            price_str=price,
            description=description,
            job_id=job_id,
            video_path=selected_video,
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

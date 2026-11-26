from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import random
import re
import sqlite3
import uuid
from pathlib import Path
from typing import Any

import cloudinary
import cloudinary.uploader
import requests
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from instagram_publisher import publish_reel, publish_story
from youtube_publisher import publish_youtube_short
from facebook_publisher import publish_facebook_reel
from reel_generator import generate_all

# Load the project .env once, before reading configuration.
load_dotenv(override=True)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("srr_bazaar_automation")

app = FastAPI(title="SRR Bazaar Product Reel Automation")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("generated")
WHATSAPP_UPLOAD_DIR = UPLOAD_DIR / "whatsapp"
WHATSAPP_OUTPUT_DIR = OUTPUT_DIR / "whatsapp"
JOB_DB_PATH = OUTPUT_DIR / "whatsapp_jobs.sqlite3"

for directory in (UPLOAD_DIR, OUTPUT_DIR, WHATSAPP_UPLOAD_DIR, WHATSAPP_OUTPUT_DIR):
    directory.mkdir(parents=True, exist_ok=True)

WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v27.0")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "").strip()
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "").strip()
META_APP_SECRET = os.getenv("META_APP_SECRET", "").strip()

# Restrict which senders can trigger a public Instagram post.
# Example .env value: WHATSAPP_ALLOWED_SENDERS=919948633303
_ALLOWED_SENDERS_RAW = os.getenv("WHATSAPP_ALLOWED_SENDERS", "").strip()
WHATSAPP_ALLOWED_SENDERS = {
    value.strip().lstrip("+")
    for value in _ALLOWED_SENDERS_RAW.split(",")
    if value.strip()
}

# Set WHATSAPP_AUTO_PUBLISH=false to generate and retain Reels without publishing.
WHATSAPP_AUTO_PUBLISH = os.getenv("WHATSAPP_AUTO_PUBLISH", "false").strip().lower() in {
    "1", "true", "yes", "on"
}

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)


def init_job_db() -> None:
    """Create a small persistent idempotency/job-status store."""
    with sqlite3.connect(JOB_DB_PATH, timeout=30) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS whatsapp_jobs (
                message_id TEXT PRIMARY KEY,
                media_id TEXT,
                sender TEXT,
                caption TEXT,
                status TEXT NOT NULL,
                image_path TEXT,
                selected_reel TEXT,
                instagram_media_id TEXT,
                error TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def claim_whatsapp_message(message: dict[str, Any]) -> bool:
    """Return True only for the first delivery of a WhatsApp message ID."""
    message_id = str(message.get("id", "")).strip()
    media_data = message.get("image") or message.get("video") or {}
    text_data = message.get("text", {})
    caption = str(media_data.get("caption", "") or text_data.get("body", "")).strip()
    if not message_id:
        return False

    with sqlite3.connect(JOB_DB_PATH, timeout=30) as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO whatsapp_jobs
                (message_id, media_id, sender, caption, status)
            VALUES (?, ?, ?, ?, 'queued')
            """,
            (
                message_id,
                str(media_data.get("id", "")),
                str(message.get("from", "")),
                caption,
            ),
        )
        connection.commit()
        return cursor.rowcount == 1


def update_whatsapp_job(message_id: str, **fields: Any) -> None:
    allowed_fields = {
        "status",
        "image_path",
        "selected_reel",
        "instagram_media_id",
        "error",
    }
    updates = {key: value for key, value in fields.items() if key in allowed_fields}
    if not updates:
        return

    assignments = ", ".join(f"{key} = ?" for key in updates)
    values = list(updates.values()) + [message_id]
    with sqlite3.connect(JOB_DB_PATH, timeout=30) as connection:
        connection.execute(
            f"UPDATE whatsapp_jobs SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE message_id = ?",
            values,
        )
        connection.commit()


init_job_db()


def upload_to_cloudinary(video_path: Path) -> str:
    result = cloudinary.uploader.upload(
        str(video_path),
        resource_type="video",
        folder="product_reels",
    )
    secure_url = result.get("secure_url")
    if not secure_url:
        raise RuntimeError("Cloudinary did not return a secure video URL")
    return secure_url


def build_instagram_caption(product_name: str, price: str, description: str, product_id: str | None = None) -> str:
    caption_parts = []
    clean_name = product_name.strip() if product_name else "Exclusive Collection"
    caption_parts.append(f"✨ {clean_name} — SRR Bazaar Sujatha Collections ✨")

    if description.strip():
        caption_parts.append(f"📝 Description:\n{description.strip()}")

    price_str = price.strip() if price else ""
    if price_str:
        if not price_str.startswith("₹"):
            price_str = f"₹{price_str}"
        caption_parts.append(
            f"🏷️ Launch Price: {price_str} ONLY\n"
            "🚚 FREE Express Shipping Pan-India\n"
            "📦 Cash on Delivery (COD) Available\n"
            "💯 100% Quality Assurance & Genuine Products Guaranteed"
        )
    else:
        caption_parts.append(
            "🚚 FREE Express Shipping Pan-India\n"
            "📦 Cash on Delivery (COD) Available\n"
            "💯 100% Quality Assurance & Genuine Products Guaranteed"
        )

    product_url = f"https://srrbazaar.com/p/{product_id}.html" if product_id else "https://srrbazaar.com"

    caption_parts.append(
        "👉 HOW TO ORDER & EXPLORE:\n"
        f"🌐 Product Link: {product_url}\n"
        "🛍️ Official Store: https://srrbazaar.com\n"
        "📸 Instagram: https://www.instagram.com/sujatha60861/\n"
        "📺 YouTube Channel & Shorts: https://www.youtube.com/@SRRBazaar\n"
        "📲 WhatsApp / Call to order directly:\n"
        "   +91 8185012453\n"
        "   +91 9948633303\n"
        "   +91 7013416296\n"
        "💬 Comment \"BUY\" below and we will DM you the direct purchase link!"
    )

    caption_parts.append(
        "#SRRBazaar #SujathaCollections #Jewellery #Sarees #PoojaSamagri #HomeSupplies "
        "#FashionJewellery #KundanJewellery #BridalJewellery #KhadiCotton #SilkSarees "
        "#IndianFashion #OnlineShoppingIndia #PanIndiaShipping #COD #Shorts #YouTubeShorts "
        "#TrendingReels #DesiShopping #BestDeals #FestiveShopping"
    )

    return "\n\n".join(caption_parts)[:2200]


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
        pn_lower = product_name.lower()
        if any(k in pn_lower for k in ["almond", "badam", "cashew", "kaju", "pista", "raisin", "walnut", "dryfruit", "date", "khajoor", "anjeer", "makhana", "vedaka", "happilo", "nut"]):
            description = (
                f"Premium {product_name} by SRR Bazaar. "
                "100% natural, vacuum-packed to preserve crunch, nutrition, and natural freshness. "
                "Express pan-India dispatch and Cash on Delivery available. Direct WhatsApp order assist: +91 8185012453."
            )
        elif any(k in pn_lower for k in ["bleach", "cleaner", "phenyl", "detergent", "acid", "disinfectant"]):
            description = (
                f"High-performance {product_name} by SRR Bazaar. "
                "Safe, powerful formulation for superior home hygiene and sanitization. "
                "Express pan-India dispatch and Cash on Delivery available. Direct WhatsApp order assist: +91 8185012453."
            )
        elif any(k in pn_lower for k in ["bulb", "led", "lighting", "electrical", "torch"]):
            description = (
                f"Energy-efficient {product_name} by SRR Bazaar. "
                "Durable build, bright illumination, and long-lasting performance. "
                "Express pan-India dispatch and Cash on Delivery available. Direct WhatsApp order assist: +91 8185012453."
            )
        elif any(k in pn_lower for k in ["saree", "sari", "cotton", "silk", "handloom"]):
            description = (
                f"Authentic handcrafted {product_name} by SRR Bazaar Sujatha Collections. "
                "Breathable premium fabric, elegant drape, and exquisite traditional craftsmanship. "
                "Express pan-India dispatch and Cash on Delivery available. Direct WhatsApp order assist: +91 8185012453."
            )
        elif any(k in pn_lower for k in ["plate", "cup", "disposable", "buffet"]):
            description = (
                f"Hygienic catering {product_name} by SRR Bazaar. "
                "Food-grade, sturdy, and eco-friendly disposable supplies. "
                "Express pan-India dispatch and Cash on Delivery available. Direct WhatsApp order assist: +91 8185012453."
            )
        else:
            description = (
                f"Exclusive {product_name} by SRR Bazaar. "
                "Premium artisanal finish, non-allergic skin-safe materials, express pan-India dispatch and Cash on Delivery available. "
                "Direct WhatsApp order assist: +91 8185012453."
            )

    price_str = f"₹{chosen_price:,}" if chosen_price else "Special Offer"
    return product_name, description, price_str


def _verify_meta_signature(raw_body: bytes, signature_header: str | None) -> None:
    """Validate Meta's X-Hub-Signature-256 when META_APP_SECRET is configured."""
    if not META_APP_SECRET:
        logger.warning(
            "META_APP_SECRET is not configured; webhook signature validation is disabled. "
            "Configure it before production deployment."
        )
        return

    if not signature_header or not signature_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Missing Meta webhook signature")

    expected = "sha256=" + hmac.new(
        META_APP_SECRET.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(status_code=401, detail="Invalid Meta webhook signature")


def regenerate_google_merchant_feed() -> None:
    """Regenerate docs/google_merchant_feed.xml from docs/products.json for Google Shopping."""
    try:
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        docs_dir = Path("docs")
        products_file = docs_dir / "products.json"
        if not products_file.exists():
            return
        products_data = json.loads(products_file.read_text(encoding="utf-8"))
        ET.register_namespace("g", "http://base.google.com/ns/1.0")

        def get_g_category(cat: str, title: str) -> str:
            t = title.lower()
            if cat == "electrical" or any(k in t for k in ["bulb", "led", "light", "electrical", "lamp", "torch", "batten"]):
                return "Home & Garden > Lighting > Light Bulbs"
            if cat == "cleaning" or any(k in t for k in ["bleach", "acid", "phenyl", "cleaner", "hygiene", "detergent", "disinfectant"]):
                return "Home & Garden > Household Supplies > Household Cleaning Supplies"
            if cat == "disposables" or any(k in t for k in ["plate", "cup", "disposable", "buffet", "leaf"]):
                return "Home & Garden > Kitchen & Dining > Tableware > Disposable Tableware"
            if cat == "dryfruits" or any(k in t for k in ["almond", "badam", "cashew", "kaju", "pista", "raisin", "walnut", "nut", "dryfruit", "dates", "khajoor", "anjeer", "makhana"]):
                return "Food, Beverages & Tobacco > Food Items > Nuts & Seeds"
            if cat in ["groceries", "snacks"] or any(k in t for k in ["grocery", "grain", "dal", "flour", "oil", "rice", "salt", "chip", "biscuit", "snack"]):
                return "Food, Beverages & Tobacco > Food Items"
            if "saree" in t or cat == "saree":
                return "Apparel & Accessories > Clothing > Traditional & Cultural Wear > Sarees"
            if cat in ["samagri", "decor"] or any(k in t for k in ["diya", "tray", "plate", "pooja", "bowl", "lotus flower", "nomu", "shatanamavali", "kadapalu", "wooden steps", "decor", "wick", "vattulu", "camphor", "dhoop"]):
                return "Home & Garden > Religious & Ceremonial"
            return "Apparel & Accessories > Jewelry"

        rss = ET.Element("rss", {"version": "2.0"})
        channel = ET.SubElement(rss, "channel")
        ET.SubElement(channel, "title").text = "SRR Bazaar — Sujatha Collections Product Feed"
        ET.SubElement(channel, "link").text = "https://srrbazaar.com"
        ET.SubElement(channel, "description").text = "Authentic Sarees, Handcrafted Bridal Jewellery, Jadau Kundan, Pooja Essentials, and Home Supplies"

        for p in products_data:
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "{http://base.google.com/ns/1.0}id").text = str(p["id"])
            clean_title = p.get("title", "").strip()
            ET.SubElement(item, "{http://base.google.com/ns/1.0}title").text = clean_title
            clean_desc = (p.get("description") or f"Exclusive {clean_title} with premium finish.").strip()
            ET.SubElement(item, "{http://base.google.com/ns/1.0}description").text = clean_desc
            canonical_url = f"https://srrbazaar.com/p/{p['id']}.html"
            ET.SubElement(item, "{http://base.google.com/ns/1.0}link").text = canonical_url
            ET.SubElement(item, "{http://base.google.com/ns/1.0}canonical_link").text = canonical_url
            img_path = p.get("image", "").lstrip("/")
            ET.SubElement(item, "{http://base.google.com/ns/1.0}image_link").text = f"https://srrbazaar.com/{img_path}"
            ET.SubElement(item, "{http://base.google.com/ns/1.0}condition").text = "new"
            ET.SubElement(item, "{http://base.google.com/ns/1.0}availability").text = "in_stock"
            ET.SubElement(item, "{http://base.google.com/ns/1.0}price").text = f"{p['price']} INR"
            ET.SubElement(item, "{http://base.google.com/ns/1.0}brand").text = "SRR Bazaar"
            ET.SubElement(item, "{http://base.google.com/ns/1.0}identifier_exists").text = "no"
            ET.SubElement(item, "{http://base.google.com/ns/1.0}google_product_category").text = get_g_category(p.get("category", ""), clean_title)
            shipping = ET.SubElement(item, "{http://base.google.com/ns/1.0}shipping")
            ET.SubElement(shipping, "{http://base.google.com/ns/1.0}country").text = "IN"
            ET.SubElement(shipping, "{http://base.google.com/ns/1.0}price").text = "0 INR"

        xml_str = ET.tostring(rss, encoding="utf-8")
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")
        (docs_dir / "google_merchant_feed.xml").write_text(pretty_xml, encoding="utf-8")
        logger.info("Auto-regenerated docs/google_merchant_feed.xml with %d products", len(products_data))
    except Exception as e:
        logger.warning("Could not regenerate google_merchant_feed.xml: %s", e)


def sync_product_to_website_catalogue(
    image_path: Path,
    product_name: str,
    price_str: str,
    description: str,
    job_id: str,
    video_path: Path | None = None,
) -> None:
    """Auto-add product to docs/products.json and docs/images/catalog/ and deploy live."""
    try:
        import subprocess
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
            # When user uploaded a VIDEO: extract representative frame from video (around 40-50% or 1s)
            vid_src = str(video_path if (video_path and Path(video_path).exists()) else image_path)
            extracted = False
            seek_t = "00:00:01"
            try:
                dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", vid_src]
                dur_res = subprocess.run(dur_cmd, capture_output=True, text=True)
                if dur_res.returncode == 0 and dur_res.stdout.strip():
                    v_dur = float(dur_res.stdout.strip())
                    if v_dur > 2.0:
                        seek_t = f"{min(v_dur * 0.5, 3.0):.2f}"
                    elif v_dur > 0.5:
                        seek_t = f"{v_dur * 0.5:.2f}"
            except Exception:
                pass

            cmd_sample = [
                "ffmpeg", "-y",
                "-ss", seek_t,
                "-i", vid_src,
                "-vframes", "1",
                "-q:v", "2",
                str(target_img_path)
            ]
            try:
                res = subprocess.run(cmd_sample, capture_output=True)
                if res.returncode == 0 and target_img_path.exists() and target_img_path.stat().st_size > 1000:
                    with open(target_img_path, "rb") as f_res:
                        if f_res.read(4).startswith(b"\xff\xd8"):
                            extracted = True
                            logger.info("Auto-extracted representative cover from video at %s: %s", seek_t, target_img_path)
            except Exception as e:
                logger.warning("Representative frame extraction attempt failed: %s", e)

            # 2. If sample failed, try 1st frame
            if not extracted:
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
                            if f_res.read(4).startswith(b"\xff\xd8"):
                                extracted = True
                                logger.info("Auto-extracted 1st frame cover from video: %s", target_img_path)
                except Exception as e:
                    logger.warning("Frame 0 extraction attempt failed: %s", e)

            # 3. If still not extracted, try quick seek fallbacks
            if not extracted:
                for fallback_t in ["00:00:00.100", "00:00:00.500"]:
                    cmd = [
                        "ffmpeg", "-y",
                        "-ss", fallback_t,
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
                                    logger.info("Auto-extracted JPEG cover from video at %s: %s", fallback_t, target_img_path)
                                    break
                    except Exception:
                        pass
            if not extracted:
                cat_cover = docs_dir / "images" / "categories" / f"cat_{category}.jpg"
                if cat_cover.exists():
                    target_img_path.write_bytes(cat_cover.read_bytes())
                    logger.warning("Video thumbnail extraction failed; fell back to category cover: %s", cat_cover)
                else:
                    fallback_img = docs_dir / "images" / "kundan_pearl_haar.jpg"
                    if fallback_img.exists():
                        target_img_path.write_bytes(fallback_img.read_bytes())
        elif image_path.exists():
            # When user uploaded a DIRECT PHOTO: Polish direct photo (EXIF orientation, vivid contrast & sharpness)
            try:
                from PIL import Image, ImageEnhance, ImageOps
                with Image.open(image_path) as im:
                    im = ImageOps.exif_transpose(im)
                    im = im.convert("RGB")
                    # Subtle direct enhancement: crisp, rich colors for jewellery & products
                    enh_c = ImageEnhance.Contrast(im).enhance(1.04)
                    enh_col = ImageEnhance.Color(enh_c).enhance(1.05)
                    enh_s = ImageEnhance.Sharpness(enh_col).enhance(1.10)
                    enh_s.save(target_img_path, "JPEG", quality=95, optimize=True)
                    logger.info("Polished and saved direct product photo: %s", target_img_path)
            except Exception as pe:
                logger.warning("PIL enhancement skipped, using direct image copy: %s", pe)
                target_img_path.write_bytes(image_path.read_bytes())

        numeric_match = re.search(r"([0-9][0-9,]*)", str(price_str).replace(",", ""))
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
        elif any(has_word(x) for x in ["almond", "almonds", "badam", "cashew", "cashews", "kaju", "pista", "pistas", "pistachio", "pistachios", "raisin", "raisins", "kishmish", "walnut", "walnuts", "akhrot", "dryfruit", "dryfruits", "date", "dates", "khajoor", "anjeer", "fig", "figs", "apricot", "apricots", "makhana", "foxnuts", "vedaka", "happilo", "farmley", "nutraj", "solimo"]) or any(has_phrase(x) for x in ["dry fruits", "dry fruit", "california almonds"]):
            category = "dryfruits"
        # 10. Snacks & Namkeen
        elif any(has_word(x) for x in ["chips", "biscuit", "biscuits", "namkeen", "mixture", "cookie", "cookies", "murukku", "sev", "bhujia", "snack", "snacks", "wafer", "wafers", "chocolate", "chocolates", "candy", "candies", "noodle", "noodles", "pasta", "maggi"]):
            category = "snacks"
        # 11. Groceries & Daily Staples (STRICT WHOLE WORD ONLY)
        elif any(has_word(x) for x in ["grocery", "groceries", "rice", "dal", "flour", "atta", "wheat", "ghee", "oil", "sunflower", "masala", "spices", "chilli", "mirchi", "turmeric", "salt", "sugar", "jaggery", "bellam", "rava", "suji", "sooji", "maida", "besan", "pulses", "lentils", "tamarind"]):
            category = "groceries"
        else:
            category = "necklace"

        new_id = int(uuid.uuid4().int % 1000000000)

        # Fallback 1: If video_path is missing/None, search in WHATSAPP_OUTPUT_DIR / job_id
        if not video_path or not Path(video_path).exists():
            job_dir = WHATSAPP_OUTPUT_DIR / job_id
            if job_dir.exists():
                candidates = list(job_dir.glob("*.mp4"))
                if candidates:
                    video_path = candidates[0]
                    logger.info("Discovered matching reel in job output dir: %s", video_path)

        # Fallback 2: Generate an on-demand reel if still missing
        if (not video_path or not Path(video_path).exists()) and image_path and Path(image_path).exists():
            try:
                from reel_generator import generate_reel
                temp_reel_dir = WHATSAPP_OUTPUT_DIR / job_id
                temp_reel_dir.mkdir(parents=True, exist_ok=True)
                video_path = generate_reel(
                    image_path=image_path,
                    product_name=product_name,
                    price=price_str or "Special Offer",
                    theme_name="minimal_premium",
                    output_dir=temp_reel_dir,
                )
                logger.info("Generated on-demand video reel fallback: %s", video_path)
            except Exception as ge:
                logger.warning("On-demand reel generation fallback failed: %s", ge)

        # Process and link matching video reel to catalogue
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
        except Exception as e_idx:
            logger.warning("Could not update DEFAULT_PRODUCTS in index.html: %s", e_idx)

        # Generate individual product share/SEO page
        try:
            from generate_product_pages import generate_all_product_pages
            generate_all_product_pages()
        except Exception as gen_err:
            logger.warning("Could not generate individual product page: %s", gen_err)

        # Auto-regenerate Google Merchant Feed XML so new product appears in Google Shopping
        try:
            regenerate_google_merchant_feed()
        except Exception as feed_err:
            logger.warning("Could not auto-regenerate google_merchant_feed.xml: %s", feed_err)

        # Auto-publish to Pinterest (if configured)
        try:
            from pinterest_publisher import publish_pin
            pin_res = publish_pin(
                title=f"{product_name} {price_str} | SRR Bazaar",
                description=description,
                product_link=f"https://srrbazaar.com/p/{new_id}.html",
                image_url=f"images/catalog/{target_img_name}",
                category=category,
            )
            if pin_res.get("status") == "published":
                logger.info("SUCCESS: Pinterest Pin published! URL: %s", pin_res.get("url"))
        except Exception as pin_err:
            logger.warning("Pinterest Pin publishing skipped/failed: %s", pin_err)

        # Deploy live to GitHub Pages and main
        try:
            subprocess.run(["git", "add", "docs/"], check=False)
            subprocess.run(["git", "commit", "-m", f"Auto-add {product_name} to website catalogue"], check=False)
            subprocess.run(["git", "push", "origin", "main"], check=False)
            
            # Robust, instant tree commit to gh-pages branch (no subtree split failures)
            tree_res = subprocess.run(["git", "rev-parse", "HEAD:docs"], capture_output=True, text=True)
            tree_hash = tree_res.stdout.strip()
            if tree_hash and len(tree_hash) == 40:
                commit_res = subprocess.run(
                    ["git", "commit-tree", tree_hash, "-m", f"Auto-deploy: {product_name}"],
                    capture_output=True, text=True
                )
                commit_hash = commit_res.stdout.strip()
                if commit_hash and len(commit_hash) == 40:
                    push_res = subprocess.run(
                        ["git", "push", "origin", f"{commit_hash}:refs/heads/gh-pages", "--force"],
                        capture_output=True
                    )
                    if push_res.returncode == 0:
                        logger.info("Auto-deployed new product '%s' to live website (gh-pages tree %s)", product_name, commit_hash[:8])
        except Exception as git_err:
            logger.warning("Git deploy skipped or failed: %s", git_err)
    except Exception as e:
        logger.warning("Could not auto-sync product to website catalogue: %s", e)


def process_whatsapp_image(message: dict[str, Any]) -> None:
    """Download a WhatsApp image or video, parse its caption, generate/extract Reel and publish."""
    message_id = str(message.get("id", "")).strip()
    media_data = message.get("image") or message.get("video") or {}
    media_id = str(media_data.get("id", "")).strip()
    sender = str(message.get("from", "")).strip().lstrip("+")
    caption = str(media_data.get("caption", "")).strip()
    image_path: Path | None = None

    try:
        if not WHATSAPP_ACCESS_TOKEN:
            raise RuntimeError("WHATSAPP_ACCESS_TOKEN is missing from .env")
        if not WHATSAPP_PHONE_NUMBER_ID:
            raise RuntimeError("WHATSAPP_PHONE_NUMBER_ID is missing from .env")
        if not media_id or not message_id:
            raise RuntimeError("WhatsApp media event is missing its message ID or media ID")

        product_name, description, price = parse_product_caption(caption)
        logger.info(
            "Parsed product from WhatsApp media %s: '%s' | Price: '%s'",
            message_id,
            product_name,
            price,
        )

        safe_message_key = hashlib.sha256(message_id.encode("utf-8")).hexdigest()[:24]
        existing_files = [f for f in WHATSAPP_UPLOAD_DIR.glob(f"{safe_message_key}.*") if f.is_file() and f.stat().st_size > 0]
        if existing_files:
            image_path = existing_files[0]
            extension = image_path.suffix.lower()
            logger.info("Using existing cached WhatsApp media on disk: %s", image_path)
        else:
            media_endpoint = (
                f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{media_id}"
            )
            auth_headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}

            media_response = requests.get(media_endpoint, headers=auth_headers, timeout=30)
            if not media_response.ok:
                raise RuntimeError(
                    f"Meta media lookup failed ({media_response.status_code}): {media_response.text[:1000]}"
                )
            media_info = media_response.json()
            media_url = media_info.get("url")
            if not media_url:
                raise RuntimeError("Meta media lookup response did not contain a download URL")

            download_response = requests.get(media_url, headers=auth_headers, timeout=60)
            if not download_response.ok:
                raise RuntimeError(
                    f"WhatsApp media download failed ({download_response.status_code}): "
                    f"{download_response.text[:500]}"
                )

            content_type = (
                str(media_info.get("mime_type") or "").split(";")[0].lower()
                or str(download_response.headers.get("Content-Type", "")).split(";")[0].lower()
            )
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
            extension = extensions.get(content_type)
            if not extension:
                if content_type.startswith("video/"):
                    extension = ".mp4"
                elif content_type.startswith("image/"):
                    extension = ".jpg"
                else:
                    raise RuntimeError(f"Unsupported WhatsApp media type: {content_type or 'unknown'}")

            image_path = WHATSAPP_UPLOAD_DIR / f"{safe_message_key}{extension}"
            image_path.write_bytes(download_response.content)
            update_whatsapp_job(message_id, image_path=str(image_path))
            logger.info("WhatsApp media downloaded: %s (%s)", image_path, content_type)

        job_id = uuid.uuid4().hex
        job_output_dir = WHATSAPP_OUTPUT_DIR / job_id
        instagram_caption = build_instagram_caption(product_name, price, description)

        header = b""
        if image_path.exists():
            with open(image_path, "rb") as f_chk:
                header = f_chk.read(16)
        is_video = (extension in {".mp4", ".mov", ".3gp", ".webm", ".avi"}) or (b"ftyp" in header or b"moov" in header)
        cover_image_path = image_path

        if is_video:
            update_whatsapp_job(message_id, status="extracting_frame")
            cover_image_path = WHATSAPP_UPLOAD_DIR / f"{safe_message_key}_thumb.jpg"
            thumb_ok = False
            # 1. Probe duration to extract representative product frame (40-50% or 1s)
            seek_t = "00:00:01"
            try:
                dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(image_path)]
                dur_res = subprocess.run(dur_cmd, capture_output=True, text=True)
                if dur_res.returncode == 0 and dur_res.stdout.strip():
                    v_dur = float(dur_res.stdout.strip())
                    if v_dur > 2.0:
                        seek_t = f"{min(v_dur * 0.5, 3.0):.2f}"
                    elif v_dur > 0.5:
                        seek_t = f"{v_dur * 0.5:.2f}"
            except Exception:
                pass

            cmd_sample = [
                "ffmpeg", "-y",
                "-ss", seek_t,
                "-i", str(image_path),
                "-vframes", "1",
                "-q:v", "2",
                str(cover_image_path)
            ]
            try:
                subprocess.run(cmd_sample, check=True, capture_output=True)
                if cover_image_path.exists() and cover_image_path.stat().st_size > 1000:
                    with open(cover_image_path, "rb") as f_res:
                        if f_res.read(4).startswith(b"\xff\xd8"):
                            thumb_ok = True
                            logger.info("Extracted representative video thumbnail at %s: %s (%d bytes)", seek_t, cover_image_path, cover_image_path.stat().st_size)
            except Exception as e:
                logger.warning("Representative frame extraction attempt failed: %s", e)

            # 2. Grab 1st frame fallback
            if not thumb_ok:
                cmd_frame0 = [
                    "ffmpeg", "-y",
                    "-i", str(image_path),
                    "-vframes", "1",
                    "-q:v", "2",
                    str(cover_image_path)
                ]
                try:
                    subprocess.run(cmd_frame0, check=True, capture_output=True)
                    if cover_image_path.exists() and cover_image_path.stat().st_size > 1000:
                        with open(cover_image_path, "rb") as f_res:
                            if f_res.read(4).startswith(b"\xff\xd8"):
                                thumb_ok = True
                                logger.info("Extracted 1st frame thumbnail: %s (%d bytes)", cover_image_path, cover_image_path.stat().st_size)
                except Exception as e:
                    logger.warning("Frame 0 thumbnail extraction attempt failed: %s", e)

            if not thumb_ok:
                for fallback_t in ["00:00:00.100", "00:00:00.500"]:
                    cmd = [
                        "ffmpeg", "-y",
                        "-ss", fallback_t,
                        "-i", str(image_path),
                        "-vframes", "1",
                        "-q:v", "2",
                        str(cover_image_path)
                    ]
                    try:
                        subprocess.run(cmd, check=True, capture_output=True)
                        if cover_image_path.exists() and cover_image_path.stat().st_size > 1000:
                            with open(cover_image_path, "rb") as f_res:
                                if f_res.read(4).startswith(b"\xff\xd8"):
                                    thumb_ok = True
                                    logger.info("Extracted video thumbnail at %s: %s (%d bytes)", fallback_t, cover_image_path, cover_image_path.stat().st_size)
                                    break
                    except Exception as e:
                        logger.warning("Could not extract frame at %s via ffmpeg: %s", fallback_t, e)

            if not thumb_ok:
                fallback_img = Path("docs/images/kundan_pearl_haar.jpg")
                if fallback_img.exists():
                    cover_image_path = fallback_img
                    logger.warning("Fell back to default catalog cover: %s", fallback_img)

            selected_reel = image_path
            update_whatsapp_job(message_id, status="video_ready", selected_reel=str(selected_reel))
        else:
            update_whatsapp_job(message_id, status="generating")
            logger.info("Generating four Reel themes for product: %s", product_name)
            generated_reels = generate_all(
                image_path=image_path,
                product_name=product_name,
                price=price or "Contact for price",
                output_dir=job_output_dir,
            )
            if len(generated_reels) != 4:
                raise RuntimeError(f"Expected four generated Reels, got {len(generated_reels)}")

            generated_reels = [Path(path) for path in generated_reels]
            selected_reel = random.choice(generated_reels)
            update_whatsapp_job(message_id, status="generated", selected_reel=str(selected_reel))
            logger.info(
                "Generated %d Reels; randomly selected %s",
                len(generated_reels),
                selected_reel.name,
            )

        if not WHATSAPP_AUTO_PUBLISH:
            update_whatsapp_job(message_id, status="preview_ready")
            logger.info("WHATSAPP_AUTO_PUBLISH=false; generated Reels retained without publishing")
            # Auto-sync product to website catalogue even if social auto-publish is off
            sync_product_to_website_catalogue(
                image_path=cover_image_path,
                product_name=product_name,
                price_str=price,
                description=description,
                job_id=job_id,
                video_path=selected_reel,
            )
            return

        update_whatsapp_job(message_id, status="uploading")
        video_url = upload_to_cloudinary(selected_reel)

        update_whatsapp_job(message_id, status="publishing")
        publish_result = publish_reel(video_url, instagram_caption)
        instagram_media_id = str(publish_result.get("media_id", ""))

        # Auto-publish to Instagram Stories
        try:
            story_res = publish_story(video_url, is_video=True)
            logger.info("SUCCESS: Instagram Story published! Media ID: %s", story_res.get("media_id"))
        except Exception as story_err:
            logger.warning("Instagram Story publishing skipped/failed: %s", story_err)

        # Auto-publish to YouTube Shorts (if configured)
        try:
            yt_title = f"{product_name} {price} | SRR Bazaar #Shorts"
            yt_res = publish_youtube_short(
                video_source=str(selected_reel),
                title=yt_title,
                description=instagram_caption,
            )
            if yt_res.get("status") == "published":
                logger.info("SUCCESS: YouTube Short published! URL: %s", yt_res.get("url"))
            else:
                logger.warning("YouTube Shorts publishing returned: %s", yt_res)
        except Exception as yt_err:
            logger.warning("YouTube Shorts publishing skipped/failed: %s", yt_err)

        # Auto-publish to Facebook Reels (if configured)
        try:
            fb_res = publish_facebook_reel(
                video_source=str(selected_reel),
                caption=instagram_caption,
            )
            if fb_res.get("status") == "published":
                logger.info("SUCCESS: Facebook Reel published! URL: %s", fb_res.get("url"))
            else:
                logger.warning("Facebook Reels publishing returned: %s", fb_res)
        except Exception as fb_err:
            logger.warning("Facebook Reels publishing skipped/failed: %s", fb_err)
        update_whatsapp_job(
            message_id,
            status="published",
            instagram_media_id=instagram_media_id,
            error=None,
        )
        logger.info(
            "SUCCESS: WhatsApp product published to Instagram. product=%s theme=%s media_id=%s sender=%s",
            product_name,
            selected_reel.stem,
            instagram_media_id,
            sender,
        )

        # Auto-sync product to website catalogue & deploy live
        sync_product_to_website_catalogue(
            image_path=cover_image_path,
            product_name=product_name,
            price_str=price,
            description=description,
            job_id=job_id,
            video_path=selected_reel,
        )

    except Exception as exc:
        update_whatsapp_job(message_id, status="failed", error=str(exc)[:2000])
        logger.exception("WhatsApp automation failed for message %s: %s", message_id, exc)


@app.get("/")
def home():
    return {
        "application": "SRR Bazaar Product Reel Automation",
        "status": "running",
        "whatsapp_auto_publish": WHATSAPP_AUTO_PUBLISH,
    }


def _parse_ai_products_and_reply(raw_reply: str) -> tuple[str, list[int]]:
    """Parse product IDs from [PRODUCTS: 123, 456] tag and return clean text with IDs."""
    product_ids: list[int] = []
    m = re.search(r'\[PRODUCTS:\s*([0-9,\s]+)\]', raw_reply)
    if m:
        ids_str = m.group(1)
        for part in ids_str.split(','):
            part_clean = part.strip()
            if part_clean.isdigit():
                product_ids.append(int(part_clean))
        clean_reply = re.sub(r'\[PRODUCTS:\s*[0-9,\s]+\]', '', raw_reply).strip()
    else:
        clean_reply = raw_reply.strip()
    return clean_reply, product_ids


def _parse_price_intent(query: str) -> tuple[float | None, float | None, str]:
    """Extract max_price, min_price, and clean query from user text."""
    q = query.lower()
    max_price = None
    min_price = None

    # Range: "between 300 and 800", "300 to 800", "300 - 800"
    m_range = re.search(r'(?:between|from)?\s*(?:rs\.?|inr|₹)?\s*([0-9]+)\s*(?:to|-|and)\s*(?:rs\.?|inr|₹)?\s*([0-9]+)', q)
    if m_range:
        p1, p2 = float(m_range.group(1)), float(m_range.group(2))
        min_price, max_price = min(p1, p2), max(p1, p2)
        q = q.replace(m_range.group(0), ' ')
    else:
        # Max price: "under 500", "below 500", "less than 500", "within 500", "500 lopala"
        m_max = re.search(r'(?:under|below|less than|within|max|upto|up to|<|<=)\s*(?:rs\.?|inr|₹)?\s*([0-9]+)', q) or \
                re.search(r'([0-9]+)\s*(?:rs\.?|inr|₹)?\s*(?:lopala|ke andar|or less)', q)
        if m_max:
            max_price = float(m_max.group(1))
            q = q.replace(m_max.group(0), ' ')

        # Min price: "above 500", "more than 500", "> 500", "min 500"
        m_min = re.search(r'(?:above|more than|over|min|from|>|>=)\s*(?:rs\.?|inr|₹)?\s*([0-9]+)', q)
        if m_min:
            min_price = float(m_min.group(1))
            q = q.replace(m_min.group(0), ' ')

    # Clean noise words
    cleaned = re.sub(r'\b(give|me|anything|something|items?|products?|collections?|show|find|search|price|inr|rs|rupees)\b', '', q).strip()
    return max_price, min_price, cleaned


def _filter_relevant_catalog(query: str, products_list: list[dict], max_items: int = 8) -> list[dict]:
    """Retrieve top relevant products for user query via price filtering and token scoring."""
    if not products_list:
        return []

    max_price, min_price, cleaned_text = _parse_price_intent(query)
    candidate_pool = products_list

    # Apply strict price filtering if requested by user
    if max_price is not None or min_price is not None:
        filtered = []
        for p in products_list:
            try:
                price = float(p.get('price', 999999))
            except Exception:
                price = 999999
            if max_price is not None and price > max_price:
                continue
            if min_price is not None and price < min_price:
                continue
            filtered.append(p)

        if filtered:
            candidate_pool = filtered
        else:
            # Fallback: return cheapest items if no items meet extreme low budget
            candidate_pool = sorted(products_list, key=lambda x: float(x.get('price', 999999)))[:max_items]

    stop_words = {"with", "this", "that", "from", "have", "image", "picture", "photo", "item", "items", "looks", "like", "also", "some", "only", "just", "show", "give", "here", "appears", "seems"}
    tokens = [t.lower() for t in re.findall(r'[a-zA-Z0-9]+', cleaned_text) if len(t) > 2 and t.lower() not in stop_words]
    if not tokens:
        # If pure budget query (e.g. "under 500"), sort by price ascending
        return sorted(candidate_pool, key=lambda x: float(x.get('price', 999999)))[:max_items]

    scored = []
    for p in candidate_pool:
        score = 0
        title_tokens = set(re.findall(r'[a-zA-Z0-9]+', p.get('title', '').lower()))
        desc_tokens = set(re.findall(r'[a-zA-Z0-9]+', f"{p.get('category', '')} {p.get('description', '')}".lower()))

        for t in tokens:
            variants = {t}
            if t.endswith('s') and len(t) > 3:
                variants.add(t[:-1])
            elif not t.endswith('s'):
                variants.add(t + 's')

            if any(v in title_tokens for v in variants):
                score += 5
            elif any(v in desc_tokens for v in variants):
                score += 2

        scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_matches = [p for score, p in scored if score > 0]
    if top_matches:
        return top_matches[:max_items]
    return candidate_pool[:max_items]


def ask_ollama_stylist(user_query: str, system_prompt: str) -> dict[str, Any] | None:
    """
    Fallback to local Ollama inference (llama3.2).
    100% free, private, and runs locally when cloud Groq is unavailable, rate-limited, or offline.
    """
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip().rstrip("/")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2").strip()
    try:
        payload = {
            "model": ollama_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            "stream": False,
            "options": {
                "temperature": 0.4,
                "num_predict": 180
            }
        }
        resp = requests.post(
            f"{ollama_base_url}/api/chat",
            json=payload,
            timeout=45
        )
        if resp.status_code == 200:
            res_json = resp.json()
            raw_reply = res_json.get("message", {}).get("content", "")
            clean_reply, product_ids = _parse_ai_products_and_reply(raw_reply)
            logger.info("Successfully generated AI response via local Ollama (%s)", ollama_model)
            return {
                "reply": clean_reply,
                "product_ids": product_ids,
                "provider": f"ollama ({ollama_model})"
            }
        else:
            logger.warning("Ollama HTTP %d: %s", resp.status_code, resp.text[:100])
            return None
    except Exception as exc:
        logger.warning("Local Ollama fallback unreachable or timed out: %s", exc)
        return None


def ask_groq_stylist(user_query: str) -> dict[str, Any]:
    """
    SRR Bazaar AI Stylist & Pooja Concierge.
    Multi-tier architecture:
    1. Primary: Groq Cloud LPU (qwen/qwen3.8-27b) for sub-second cloud responses.
    2. Fallback: Local Ollama (llama3.2) when Groq is unavailable, out of quota, or offline.
    3. Final Fallback: Curated catalog matching.
    """
    clean_query = user_query.strip()
    if not clean_query:
        return {
            "reply": "Namaste! Welcome to SRR Bazaar (Sujatha Collections). Please ask me about bridal jewellery, Sankranti pooja items, sarees, order tracking, or wholesale items!",
            "product_ids": []
        }

    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()

    # Load catalogue from docs/products.json
    products_file = Path("docs/products.json")
    products_list = []
    if products_file.exists():
        try:
            products_list = json.loads(products_file.read_text(encoding="utf-8"))
        except Exception:
            products_list = []

    # Filter catalog to top relevant items to maximize LLM speed and prevent timeouts
    relevant_products = _filter_relevant_catalog(clean_query, products_list, max_items=8)
    catalog_summary = "\n".join([
        f"- ID: {p.get('id')} | {p.get('title')} | Rs {p.get('price')}"
        for p in relevant_products
    ])

    system_prompt = f"""You are the official AI Shopping Stylist and Festive Concierge for SRR Bazaar (Sujatha Collections), based in Telangana.
Logistics Partner: The Professional Couriers (Armoor Hub). Free express delivery across India. Cash on Delivery (COD) available.
Direct WhatsApp assist: +91 8185012453 | Helpline: +91 9948633303 | Website: https://srrbazaar.com

Active store catalogue:
{catalog_summary}

Instructions:
1. Reply warmly in 2-4 friendly, concise sentences. Respond in the customer's language (English, Telugu, or Hindi).
2. If they ask for recommendations or items: Recommend 1 to 3 specific products from the catalogue that fit their request, occasion, or budget.
3. If they ask about special occasions (e.g. Satyanarayana pooja with guest dining, or bridal look for maroon/silk saree), dynamically recommend a complete combo bundle (e.g. Diya Stand + Lotus Plate + Leaf Plates, or Kundan Choker + Jhumkas) with combo package savings!
4. If they ask about order tracking / shipping: Explain that all orders are dispatched same-day via The Professional Couriers (Armoor Hub) and can be tracked at https://www.tpcindia.com/. Invite them to share their consignment number or city for instant status.
5. At the very end of your response, if you recommended products, append the product IDs formatted exactly as:
[PRODUCTS: id1, id2]
Example: [PRODUCTS: 703481457, 592133224]"""

    # Tier 1: Groq Cloud LPU
    if groq_api_key:
        try:
            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json",
                "User-Agent": "SRR-Bazaar/1.0"
            }
            data = {
                "model": "qwen/qwen3.8-27b",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": clean_query}
                ],
                "max_tokens": 300,
                "temperature": 0.5
            }
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            if resp.status_code == 200:
                res_json = resp.json()
                raw_reply = res_json["choices"][0]["message"].get("content", "")
                clean_reply, product_ids = _parse_ai_products_and_reply(raw_reply)
                return {"reply": clean_reply, "product_ids": product_ids, "provider": "groq"}
            else:
                logger.warning(
                    "Groq API returned HTTP %d: %s. Falling back to local Ollama (llama3.2)...",
                    resp.status_code, resp.text[:120]
                )
        except Exception as exc:
            logger.warning("Groq API request failed (%s). Falling back to local Ollama (llama3.2)...", exc)
    else:
        logger.info("GROQ_API_KEY not configured. Falling back to local Ollama (llama3.2)...")

    # Tier 2: Local Ollama (llama3.2) Fallback
    ollama_result = ask_ollama_stylist(clean_query, system_prompt)
    if ollama_result:
        return ollama_result

    # Tier 3: Static Curated Catalog Fallback (if both Groq and Ollama are unavailable)
    logger.warning("Both Groq and local Ollama are unavailable; using catalog heuristic fallback.")
    return {
        "reply": "Namaste! Welcome to SRR Bazaar. Our festive recommendations include Edu Kondala Nomu, 33 Diya Stand, and Kundan Chokers with Free Express Delivery via The Professional Couriers!",
        "product_ids": [592133224, 703481457, 378586240],
        "provider": "static_fallback"
    }


def send_whatsapp_text(to_number: str, message_text: str) -> bool:
    """Send a direct WhatsApp text reply to a customer via Meta WhatsApp Cloud API."""
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.warning("WhatsApp credentials missing; cannot send direct reply.")
        return False

    url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {"preview_url": True, "body": message_text},
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code in (200, 201):
            logger.info("Successfully sent WhatsApp reply to %s", to_number)
            return True
        else:
            logger.error(
                "Failed to send WhatsApp message to %s (%d): %s",
                to_number,
                resp.status_code,
                resp.text,
            )
            return False
    except Exception as exc:
        logger.exception("Error sending WhatsApp message to %s: %s", to_number, exc)
        return False


def format_whatsapp_reply_with_links(reply_text: str, product_ids: list[int]) -> str:
    """Format AI Stylist reply for WhatsApp text message with store links and product details."""
    parts = [reply_text]

    # If product IDs recommended, attach their titles, prices and website links
    if product_ids:
        products_file = Path("docs/products.json")
        if products_file.exists():
            try:
                products_list = json.loads(products_file.read_text(encoding="utf-8"))
                matched = [p for p in products_list if p.get("id") in product_ids][:3]
                if matched:
                    parts.append("\n🛍️ Recommended Collections:")
                    for p in matched:
                        title = p.get("title", "")
                        price = p.get("price", 0)
                        parts.append(f"• {title} — ₹{price}")
            except Exception:
                pass

    parts.append(
        "\n🌐 View & Order Online: https://srrbazaar.com\n"
        "🚚 Free Express Delivery via The Professional Couriers (Armoor Hub)\n"
        "📦 COD Available | Support: +91 9948633303"
    )
    return "\n".join(parts).strip()


def handle_whatsapp_customer_reply(sender: str, user_text: str, message_id: str | None = None) -> None:
    """Process incoming customer question with Groq and send direct reply back to their WhatsApp."""
    try:
        logger.info("Processing customer WhatsApp message from %s: '%s'", sender, user_text)
        result = ask_groq_stylist(user_text)
        formatted_reply = format_whatsapp_reply_with_links(
            result.get("reply", ""),
            result.get("product_ids", [])
        )
        success = send_whatsapp_text(to_number=sender, message_text=formatted_reply)
        if success and message_id:
            update_whatsapp_job(message_id, status="replied")
    except Exception as exc:
        logger.exception("Failed customer WhatsApp reply to %s: %s", sender, exc)
        if message_id:
            update_whatsapp_job(message_id, status="failed", error=str(exc)[:500])


@app.post("/api/ai-stylist")
async def ai_stylist_endpoint(request: Request):
    """
    SRR Bazaar AI Stylist & Pooja Concierge API endpoint for website.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    user_query = str(body.get("message", "")).strip()
    return ask_groq_stylist(user_query)


def ask_ollama_vision(image_bytes: bytes) -> tuple[str, list[dict[str, Any]]]:
    """
    Use local Ollama vision model (llava-phi3) to inspect uploaded image,
    extract keywords, and retrieve matching products from the store catalogue.
    """
    import base64
    b64 = base64.b64encode(image_bytes).decode()

    # Load catalogue
    products_file = Path("docs/products.json")
    products_list = []
    if products_file.exists():
        try:
            products_list = json.loads(products_file.read_text(encoding="utf-8"))
        except Exception:
            products_list = []

    vision_model = os.getenv("OLLAMA_VISION_MODEL", "llava-phi3")
    prompt = (
        "Inspect this image carefully. Is it traditional Indian jewelry (necklace, earrings, choker, mangalsutra), "
        "pooja brassware (diya stand, plate, tray), dining (leaf plates), or a non-catalog document/screenshot? "
        "Give a concise 1-2 sentence description and 3-5 search keywords."
    )

    try:
        resp = requests.post(
            f"{os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/')}/api/generate",
            json={
                "model": vision_model,
                "prompt": prompt,
                "images": [b64],
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 100
                }
            },
            timeout=70
        )
        if resp.status_code == 200:
            content = resp.json().get("response", "").strip()
            lower_content = content.lower()
            if any(term in lower_content for term in ["document", "screenshot", "form", "text", "receipt", "invoice", "application"]):
                desc = "I inspected your image and noticed it appears to be a document or screenshot rather than a jewelry or pooja piece. Here are SRR Bazaar's authentic handcrafted collections:"
                return desc, products_list[:4]

            matches = _filter_relevant_catalog(content, products_list, max_items=4)
            return content, matches
    except Exception as e:
        logger.warning("Local Ollama vision failed: %s", e)

    return "Handcrafted festive jewellery & pooja collections", products_list[:4]


@app.post("/api/visual-search")
async def visual_search_endpoint(file: UploadFile = File(...)):
    """
    Inspect an uploaded photo with local Ollama minicpm-v vision model
    and return closest matching items in SRR Bazaar catalogue.
    """
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image file uploaded")
    detected_desc, matches = ask_ollama_vision(contents)
    return {
        "status": "success",
        "description": detected_desc,
        "product_ids": [p.get("id") for p in matches],
        "products": matches
    }


@app.post("/publish")
async def publish_product(
    photo: UploadFile = File(...),
    product_name: str = Form("Beautiful Jewellery"),
    price: str = Form(""),
    description: str = Form(""),
):
    if photo.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Upload a JPG, PNG or WebP image")

    job_id = uuid.uuid4().hex
    photo_path = UPLOAD_DIR / f"{job_id}.jpg"
    job_output_dir = OUTPUT_DIR / job_id

    try:
        from PIL import Image

        image = Image.open(photo.file).convert("RGB")
        image.save(photo_path, "JPEG", quality=95)

        caption = build_instagram_caption(product_name, price, description)
        generated_reels = generate_all(
            image_path=photo_path,
            product_name=product_name,
            price=price or "Contact for price",
            output_dir=job_output_dir,
        )
        if len(generated_reels) != 4:
            raise RuntimeError(f"Expected 4 generated Reels, got {len(generated_reels)}")

        selected_reel = Path(random.choice(generated_reels))
        video_url = upload_to_cloudinary(selected_reel)
        publish_result = publish_reel(video_url, caption)

        # Auto-publish to Instagram Stories
        try:
            publish_story(video_url, is_video=True)
        except Exception as story_err:
            logger.warning("Instagram Story publishing skipped/failed: %s", story_err)

        return {
            "success": True,
            "job_id": job_id,
            "product": product_name,
            "generated_count": len(generated_reels),
            "generated_reels": [str(path) for path in generated_reels],
            "selected_reel": str(selected_reel),
            "selected_theme": selected_reel.stem,
            "instagram_media_id": publish_result["media_id"],
            "container_id": publish_result["container_id"],
            "message": "One randomly selected Reel was published successfully.",
        }
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
    finally:
        photo_path.unlink(missing_ok=True)


@app.get("/webhook")
async def verify_whatsapp_webhook(request: Request):
    params = request.query_params
    if (
        params.get("hub.mode") == "subscribe"
        and WHATSAPP_VERIFY_TOKEN
        and hmac.compare_digest(params.get("hub.verify_token", ""), WHATSAPP_VERIFY_TOKEN)
    ):
        return PlainTextResponse(params.get("hub.challenge", ""))
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@app.post("/webhook")
async def receive_whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    raw_body = await request.body()
    _verify_meta_signature(raw_body, request.headers.get("X-Hub-Signature-256"))

    try:
        payload = json.loads(raw_body or b"{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    queued = 0
    ignored = 0

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            metadata = value.get("metadata", {})
            received_phone_number_id = str(metadata.get("phone_number_id", ""))

            if (
                WHATSAPP_PHONE_NUMBER_ID
                and received_phone_number_id
                and received_phone_number_id != WHATSAPP_PHONE_NUMBER_ID
            ):
                logger.warning(
                    "Ignoring webhook for unexpected phone number ID %s",
                    received_phone_number_id,
                )
                ignored += 1
                continue

            for message in value.get("messages", []):
                msg_type = message.get("type")
                sender = str(message.get("from", "")).strip().lstrip("+")
                message_id = str(message.get("id", "")).strip()

                # Case 1: Media (Image / Video) from Admin -> Product Reel Generation & Store Sync
                if msg_type in ("image", "video"):
                    if WHATSAPP_ALLOWED_SENDERS and sender not in WHATSAPP_ALLOWED_SENDERS:
                        logger.warning("Ignoring media from sender not in WHATSAPP_ALLOWED_SENDERS: %s", sender)
                        ignored += 1
                        continue

                    if claim_whatsapp_message(message):
                        background_tasks.add_task(process_whatsapp_image, message)
                        queued += 1
                    else:
                        logger.info("Ignoring duplicate WhatsApp media delivery: %s", message_id)
                        ignored += 1
                    continue

                # Case 2: Customer Text or Interactive Inquiry -> Groq AI Concierge Auto-Reply
                if msg_type in ("text", "interactive"):
                    user_text = ""
                    if msg_type == "text":
                        user_text = str(message.get("text", {}).get("body", "")).strip()
                    elif msg_type == "interactive":
                        interactive = message.get("interactive", {})
                        user_text = (
                            interactive.get("button_reply", {}).get("title")
                            or interactive.get("list_reply", {}).get("title")
                            or ""
                        ).strip()

                    if not user_text:
                        ignored += 1
                        continue

                    if claim_whatsapp_message(message):
                        background_tasks.add_task(handle_whatsapp_customer_reply, sender, user_text, message_id)
                        queued += 1
                    else:
                        logger.info("Ignoring duplicate WhatsApp customer message: %s", message_id)
                        ignored += 1
                    continue

                # Unhandled message types
                ignored += 1

    # Respond immediately. Media processing & AI replies run asynchronously in background.
    return {"status": "received", "queued_tasks": queued, "ignored_events": ignored}


# =============================================================================
# REAL-TIME UNIQUE SPIN REFERRAL & DEVICE CLICK TRACKER
# =============================================================================
spin_token_clicks: dict[str, set[str]] = {}

@app.post("/api/spin-ref/click")
async def register_spin_click(request: Request):
    try:
        data = await request.json()
        token = data.get("token", "").strip()
        device_id = data.get("deviceId", "").strip()
        if not token or not device_id:
            return {"status": "error", "message": "Missing token or deviceId"}
        if token not in spin_token_clicks:
            spin_token_clicks[token] = set()
        spin_token_clicks[token].add(device_id)
        count = len(spin_token_clicks[token])
        return {
            "status": "success",
            "token": token,
            "count": count,
            "unlocked": count >= 2
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/spin-ref/status/{token}")
async def get_spin_status(token: str):
    token = token.strip()
    devices = spin_token_clicks.get(token, set())
    count = len(devices)
    return {
        "status": "success",
        "token": token,
        "count": count,
        "unlocked": count >= 2
    }

# Mount docs directory so local server can serve storefront, images, and videos
from fastapi.staticfiles import StaticFiles
if Path("docs").exists():
    app.mount("/", StaticFiles(directory="docs", html=True), name="static")


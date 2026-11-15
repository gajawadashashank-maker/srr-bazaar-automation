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
from fastapi.responses import PlainTextResponse

from instagram_publisher import publish_reel
from reel_generator import generate_all

# Load the project .env once, before reading configuration.
load_dotenv(override=True)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("srr_bazaar_automation")

app = FastAPI(title="SRR Bazaar Product Reel Automation")

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
    image_data = message.get("image") or {}
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
                str(image_data.get("id", "")),
                str(message.get("from", "")),
                str(image_data.get("caption", "")),
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
    """Parse either labelled captions or simple lines like name / details / @1199 rs."""
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
        # Also accept a plain numeric price on its own line, but only after a product name exists.
        if found_price is None and product_name:
            bare_amount = re.fullmatch(r"\s*(?:₹\s*)?([0-9][0-9,]*(?:\.[0-9]{1,2})?)\s*", line)
            if bare_amount:
                found_price = bare_amount.group(1)
                bare_price_only = True
        if found_price is not None:
            price = _normalise_price(found_price)
            # Dedicated price-only lines contain no description text to preserve.
            if bare_price_only or re.match(r"(?i)^\s*price\s*[:\-]?", line):
                continue
            # If a price is embedded in a descriptive line, retain the non-price words.
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
        # A caption containing only a bare number is almost certainly a price, not a product name.
        if re.fullmatch(r"[₹\s]*[0-9][0-9,.]*", product_name):
            product_name = None

    description = "\n".join(description_lines).strip()
    return product_name, description, price


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


def process_whatsapp_image(message: dict[str, Any]) -> None:
    """Download a WhatsApp image, parse its caption, generate four Reels and publish one."""
    message_id = str(message.get("id", "")).strip()
    image_data = message.get("image") or {}
    media_id = str(image_data.get("id", "")).strip()
    sender = str(message.get("from", "")).strip().lstrip("+")
    caption = str(image_data.get("caption", "")).strip()
    image_path: Path | None = None

    try:
        if not WHATSAPP_ACCESS_TOKEN:
            raise RuntimeError("WHATSAPP_ACCESS_TOKEN is missing from .env")
        if not WHATSAPP_PHONE_NUMBER_ID:
            raise RuntimeError("WHATSAPP_PHONE_NUMBER_ID is missing from .env")
        if not media_id or not message_id:
            raise RuntimeError("WhatsApp image event is missing its message ID or media ID")

        product_name, description, price = parse_product_caption(caption)
        if not product_name:
            update_whatsapp_job(
                message_id,
                status="needs_caption",
                error="No product name found. Forward one image with a caption containing the product name.",
            )
            logger.warning(
                "WhatsApp image %s saved for review but not published: caption has no product name",
                message_id,
            )

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
        }
        extension = extensions.get(content_type)
        if not extension:
            raise RuntimeError(f"Unsupported WhatsApp image type: {content_type or 'unknown'}")

        safe_message_key = hashlib.sha256(message_id.encode("utf-8")).hexdigest()[:24]
        image_path = WHATSAPP_UPLOAD_DIR / f"{safe_message_key}{extension}"
        image_path.write_bytes(download_response.content)
        update_whatsapp_job(message_id, image_path=str(image_path))
        logger.info("WhatsApp image downloaded: %s", image_path)

        if not product_name:
            return

        job_id = uuid.uuid4().hex
        job_output_dir = WHATSAPP_OUTPUT_DIR / job_id
        instagram_caption = build_instagram_caption(product_name, price, description)

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
            return

        update_whatsapp_job(message_id, status="uploading")
        video_url = upload_to_cloudinary(selected_reel)

        update_whatsapp_job(message_id, status="publishing")
        publish_result = publish_reel(video_url, instagram_caption)
        instagram_media_id = str(publish_result.get("media_id", ""))
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
                if message.get("type") != "image":
                    ignored += 1
                    continue

                sender = str(message.get("from", "")).strip().lstrip("+")
                if WHATSAPP_ALLOWED_SENDERS and sender not in WHATSAPP_ALLOWED_SENDERS:
                    logger.warning("Ignoring image from sender not in WHATSAPP_ALLOWED_SENDERS")
                    ignored += 1
                    continue

                if claim_whatsapp_message(message):
                    background_tasks.add_task(process_whatsapp_image, message)
                    queued += 1
                else:
                    logger.info("Ignoring duplicate WhatsApp message delivery: %s", message.get("id"))
                    ignored += 1

    # Respond immediately. Media download, FFmpeg, Cloudinary and Instagram run after the ACK.
    return {"status": "received", "queued_images": queued, "ignored_events": ignored}

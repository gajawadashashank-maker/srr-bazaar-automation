import os
import uuid
import random
from pathlib import Path

import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException

from reel_generator import generate_all
from instagram_publisher import publish_reel

import os
import hmac
import requests

from fastapi import Request
from fastapi.responses import PlainTextResponse

from dotenv import load_dotenv

load_dotenv(override=True)

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v27.0")

load_dotenv()
app = FastAPI(title="SRR Bazaar Product Reel Automation")
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("generated")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)


def upload_to_cloudinary(video_path: Path) -> str:
    result = cloudinary.uploader.upload(str(video_path), resource_type="video", folder="product_reels")
    return result["secure_url"]


@app.get("/")
def home():
    return {"application": "SRR Bazaar Product Reel Automation", "status": "running"}


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

        caption_parts = [product_name]
        if description.strip():
            caption_parts.append(description.strip())
        if price.strip():
            caption_parts.append(f"Price: {price.strip()}")
        caption_parts.extend(["DM us to order 💌", "#SRRBazaar #Shopping #IndianFashion #OnlineShopping"])
        caption = "\n\n".join(caption_parts)[:2200]

        # Generate and retain all four existing theme videos for this job.
        generated_reels = generate_all(
            image_path=photo_path,
            product_name=product_name,
            price=price or "Contact for price",
            output_dir=job_output_dir,
        )
        if len(generated_reels) != 4:
            raise RuntimeError(f"Expected 4 generated Reels, got {len(generated_reels)}")

        # Randomly choose exactly one; the other three remain in generated/<job_id>/.
        selected_reel = random.choice(generated_reels)
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


WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

WHATSAPP_API_VERSION = "v25.0"

WHATSAPP_UPLOAD_DIR = UPLOAD_DIR / "whatsapp"
WHATSAPP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/webhook")
async def verify_whatsapp_webhook(request: Request):
    params = request.query_params

    if (
        params.get("hub.mode") == "subscribe"
        and hmac.compare_digest(
            params.get("hub.verify_token", ""),
            WHATSAPP_VERIFY_TOKEN or ""
        )
    ):
        return PlainTextResponse(params.get("hub.challenge", ""))

    raise HTTPException(status_code=403, detail="Webhook verification failed")


@app.post("/webhook")
async def receive_whatsapp_webhook(request: Request):
    payload = await request.json()
    print("\n========== WHATSAPP WEBHOOK ==========")
    print(payload)
    print("======================================\n")

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})

            for message in value.get("messages", []):
                if message.get("type") != "image":
                    continue

                media_id = message["image"]["id"]
                message_id = message["id"]

                # Retrieve temporary media URL from Meta
                media_response = requests.get(
                    f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{media_id}",
                    headers={
                        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
                    },
                    timeout=30,
                )
                print(
                    "MEDIA API RESPONSE:",
                     media_response.status_code,
                     media_response.text
                )
                media_response.raise_for_status()

                media_url = media_response.json()["url"]

                # Download actual image
                image_response = requests.get(
                    media_url,
                    headers={
                        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
                    },
                    timeout=60,
                )
                image_response.raise_for_status()

                content_type = image_response.headers.get("Content-Type", "")

                extensions = {
                    "image/jpeg": ".jpg",
                    "image/png": ".png",
                    "image/webp": ".webp",
                }

                extension = extensions.get(content_type.split(";")[0].lower())

                if not extension:
                    continue

                image_path = WHATSAPP_UPLOAD_DIR / f"{message_id}{extension}"
                image_path.write_bytes(image_response.content)

                print(f"WhatsApp image saved: {image_path}")

    return {"status": "received"}



import os
import uuid
import time
import subprocess
from pathlib import Path

import requests
import cloudinary
import cloudinary.uploader

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException

load_dotenv()

app = FastAPI(title="Product Reel Automation")

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("generated")

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

IG_ID = os.getenv("IG_USER_ID")
IG_TOKEN = os.getenv("IG_ACCESS_TOKEN")
API_VERSION = os.getenv("GRAPH_API_VERSION")

MUSIC_FILE = Path(os.getenv("MUSIC_FILE", "music/background.mp3"))

BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


def generate_reel(photo_path: Path, video_path: Path):
    """Create an 8-second vertical product video."""

    if not MUSIC_FILE.exists():
        raise FileNotFoundError("Background music file not found")

    command = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(photo_path),
        "-stream_loop", "-1",
        "-i", str(MUSIC_FILE),
        "-t", "8",
        "-vf",
        (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "zoompan=z='min(zoom+0.0008,1.08)':"
            "d=240:s=1080x1920:fps=30,"
            "format=yuv420p"
        ),
        "-r", "30",
        "-c:v", "libx264",
        "-preset", "medium",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "48000",
        "-shortest",
        "-movflags", "+faststart",
        str(video_path)
    ]

    subprocess.run(command, check=True)


def upload_to_cloudinary(video_path: Path) -> str:
    """Upload video and obtain a public HTTPS URL."""

    result = cloudinary.uploader.upload(
        str(video_path),
        resource_type="video",
        folder="product_reels"
    )

    return result["secure_url"]


def publish_instagram_reel(video_url: str, caption: str):
    """Create and publish Instagram Reel."""

    headers = {
        "Authorization": f"Bearer {IG_TOKEN}"
    }

    # Create media container
    response = requests.post(
        f"{BASE_URL}/{IG_ID}/media",
        headers=headers,
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true"
        },
        timeout=60
    )

    response.raise_for_status()
    container_id = response.json()["id"]

    # Wait until Instagram processes video
    for attempt in range(36):
        status_response = requests.get(
            f"{BASE_URL}/{container_id}",
            headers=headers,
            params={"fields": "status_code"},
            timeout=30
        )

        status_response.raise_for_status()
        status = status_response.json()["status_code"]

        if status == "FINISHED":
            break

        if status == "ERROR":
            raise RuntimeError("Instagram video processing failed")

        time.sleep(5)

    else:
        raise TimeoutError("Instagram processing timed out")

    # Publish Reel
    publish_response = requests.post(
        f"{BASE_URL}/{IG_ID}/media_publish",
        headers=headers,
        data={"creation_id": container_id},
        timeout=60
    )

    publish_response.raise_for_status()

    return publish_response.json()


@app.get("/")
def home():
    return {
        "application": "Product Reel Automation",
        "status": "running"
    }


@app.post("/publish")
async def publish_product(
    photo: UploadFile = File(...),
    product_name: str = Form("Beautiful Jewellery"),
    price: str = Form(""),
    description: str = Form("")
):
    if photo.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(400, "Upload a JPG, PNG or WebP image")

    job_id = uuid.uuid4().hex

    photo_path = UPLOAD_DIR / f"{job_id}.jpg"
    video_path = OUTPUT_DIR / f"{job_id}.mp4"

    try:
        # Normalize the image to JPEG
        from PIL import Image

        image = Image.open(photo.file).convert("RGB")
        image.save(photo_path, "JPEG", quality=95)

        # Prepare Instagram caption
        caption = (
            f"{product_name}\n\n"
            f"{description}\n\n"
            f"Price: {price}\n\n"
            "DM us to order 💌\n\n"
            "#Jewellery #Fashion #Shopping "
            "#IndianJewellery #OnlineShopping"
        )

        # Generate Reel
        generate_reel(photo_path, video_path)

        # Upload video
        video_url = upload_to_cloudinary(video_path)

        # Publish Reel
        result = publish_instagram_reel(
            video_url,
            caption[:2200]
        )

        return {
            "success": True,
            "job_id": job_id,
            "instagram_media_id": result.get("id"),
            "product": product_name
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:
        photo_path.unlink(missing_ok=True)
        video_path.unlink(missing_ok=True)

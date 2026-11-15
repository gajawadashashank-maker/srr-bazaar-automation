
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_VERSION = os.getenv("META_API_VERSION", "v27.0")
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

IG_USER_ID = os.getenv("INSTAGRAM_USER_ID")
ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")

def publish_reel(video_url: str, caption: str):
    # 1. Create Reel container
    response = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": ACCESS_TOKEN,
        },
        timeout=60,
    )
    response.raise_for_status()
    container_id = response.json()["id"]

    # 2. Wait until Meta finishes processing
    for _ in range(30):
        status_response = requests.get(
            f"{BASE_URL}/{container_id}",
            params={
                "fields": "status_code,status",
                "access_token": ACCESS_TOKEN,
            },
            timeout=30,
        )
        status_response.raise_for_status()
        status = status_response.json()

        if status.get("status_code") == "FINISHED":
            break

        if status.get("status_code") == "ERROR":
            raise RuntimeError(status)

        time.sleep(10)
    else:
        raise TimeoutError("Instagram video processing timed out")

    # 3. Publish Reel
    publish_response = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": ACCESS_TOKEN,
        },
        timeout=60,
    )
    publish_response.raise_for_status()

    return publish_response.json()
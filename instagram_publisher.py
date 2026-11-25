import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
API_VERSION = os.getenv("META_API_VERSION") or os.getenv("GRAPH_API_VERSION", "v25.0")
if API_VERSION in ("vXX.X", "XX.X", ""):
    API_VERSION = "v25.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"
IG_USER_ID = os.getenv("META_INSTAGRAM_ACCOUNT_ID")
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")


def publish_reel(video_url: str, caption: str):
    if not IG_USER_ID or not ACCESS_TOKEN:
        raise RuntimeError("META_INSTAGRAM_ACCOUNT_ID or META_ACCESS_TOKEN missing from .env")

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    response = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media",
        headers=headers,
        data={"media_type": "REELS", "video_url": video_url, "caption": caption, "share_to_feed": "true"},
        timeout=60,
    )
    response.raise_for_status()
    container_id = response.json()["id"]

    # Poll processing status with a bounded wait; publish only when FINISHED.
    for _ in range(36):
        status_response = requests.get(
            f"{BASE_URL}/{container_id}",
            headers=headers,
            params={"fields": "status_code,status"},
            timeout=30,
        )
        status_response.raise_for_status()
        status_data = status_response.json()
        status = status_data.get("status_code")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram container {status}: {status_data.get('status', '')}")
        time.sleep(5)
    else:
        raise TimeoutError("Instagram video processing timed out; container was not published")

    publish_response = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media_publish",
        headers=headers,
        data={"creation_id": container_id},
        timeout=60,
    )
    publish_response.raise_for_status()
    return {"container_id": container_id, "media_id": publish_response.json().get("id")}


def publish_story(media_url: str, is_video: bool = True):
    """Publish a 9:16 video or image directly to Instagram Stories."""
    if not IG_USER_ID or not ACCESS_TOKEN:
        raise RuntimeError("META_INSTAGRAM_ACCOUNT_ID or META_ACCESS_TOKEN missing from .env")

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    payload = {"media_type": "STORIES"}
    if is_video:
        payload["video_url"] = media_url
    else:
        payload["image_url"] = media_url

    response = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media",
        headers=headers,
        data=payload,
        timeout=60,
    )
    response.raise_for_status()
    container_id = response.json()["id"]

    # Poll processing status with a bounded wait; publish only when FINISHED.
    for _ in range(36):
        status_response = requests.get(
            f"{BASE_URL}/{container_id}",
            headers=headers,
            params={"fields": "status_code,status"},
            timeout=30,
        )
        status_response.raise_for_status()
        status_data = status_response.json()
        status = status_data.get("status_code")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram Story container {status}: {status_data.get('status', '')}")
        time.sleep(5)
    else:
        raise TimeoutError("Instagram Story processing timed out; container was not published")

    publish_response = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media_publish",
        headers=headers,
        data={"creation_id": container_id},
        timeout=60,
    )
    publish_response.raise_for_status()
    return {"container_id": container_id, "media_id": publish_response.json().get("id")}

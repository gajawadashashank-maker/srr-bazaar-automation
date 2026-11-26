import os
import time
import logging
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger("facebook_publisher")

FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "1509066322281674")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
API_VERSION = os.getenv("META_API_VERSION", "v25.0")
if API_VERSION in ("vXX.X", "XX.X", ""):
    API_VERSION = "v25.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"


def publish_facebook_reel(video_source: str, caption: str) -> dict:
    """
    Publish a vertical 9:16 video reel directly to the Facebook Page.
    video_source: local file path or http(s) URL.
    caption: text description for the Facebook Reel post.
    """
    token = os.getenv("META_ACCESS_TOKEN") or META_ACCESS_TOKEN
    page_id = os.getenv("FACEBOOK_PAGE_ID") or FACEBOOK_PAGE_ID

    if not token or not page_id:
        logger.info("Facebook Page ID or Meta Token not configured. Skipping Facebook Reels upload.")
        return {"status": "skipped", "reason": "credentials_not_configured"}

    # Prepare local video path
    temp_download = False
    local_path = None
    if video_source.startswith("http://") or video_source.startswith("https://"):
        temp_download = True
        local_path = Path("temp_fb_upload.mp4")
        logger.info("Downloading remote video for Facebook upload from %s...", video_source)
        res = requests.get(video_source, stream=True, timeout=120)
        res.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    else:
        local_path = Path(video_source)

    if not local_path.exists():
        logger.error("Video file %s not found for Facebook upload.", local_path)
        return {"status": "error", "error": f"File {local_path} not found"}

    try:
        file_size = local_path.stat().st_size

        # Phase 1: Initialize Upload Session
        init_url = f"{BASE_URL}/{page_id}/video_reels"
        headers = {"Authorization": f"Bearer {token}"}
        init_payload = {"upload_phase": "start"}

        init_res = requests.post(init_url, headers=headers, json=init_payload, timeout=30)
        init_data = init_res.json()

        if "error" in init_data:
            err_msg = init_data["error"].get("message", "")
            logger.warning("Facebook Reels Init returned error: %s", err_msg)
            return {"status": "error", "error": err_msg, "code": init_data["error"].get("code")}

        video_id = init_data.get("video_id")
        upload_url = init_data.get("upload_url")
        if not video_id or not upload_url:
            return {"status": "error", "error": "Missing video_id or upload_url in Facebook response"}

        # Phase 2: Upload Video Bytes
        upload_headers = {
            "Authorization": f"OAuth {token}",
            "offset": "0",
            "file_size": str(file_size),
        }
        with open(local_path, "rb") as video_file:
            upload_res = requests.post(upload_url, headers=upload_headers, data=video_file, timeout=300)
            upload_res.raise_for_status()

        # Phase 3: Finish and Publish
        publish_payload = {
            "upload_phase": "finish",
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "description": caption,
        }
        publish_res = requests.post(init_url, headers=headers, json=publish_payload, timeout=60)
        publish_res.raise_for_status()
        pub_data = publish_res.json()

        if pub_data.get("success"):
            fb_url = f"https://www.facebook.com/reel/{video_id}"
            logger.info("SUCCESS: Facebook Reel published! ID: %s, URL: %s", video_id, fb_url)
            return {"status": "published", "video_id": video_id, "url": fb_url}
        else:
            return {"status": "error", "error": str(pub_data)}

    except Exception as exc:
        logger.error("Failed to publish Facebook Reel: %s", exc)
        return {"status": "error", "error": str(exc)}

    finally:
        if temp_download and local_path and local_path.exists():
            try:
                local_path.unlink()
            except Exception:
                pass

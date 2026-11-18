import os
import logging
from pathlib import Path
from typing import Optional
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("youtube_publisher")

YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN")


def get_youtube_access_token() -> Optional[str]:
    """Exchange refresh token for an active Google OAuth2 access token."""
    if not (YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET and YOUTUBE_REFRESH_TOKEN):
        logger.warning("YouTube credentials (CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN) not configured.")
        return None

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": YOUTUBE_CLIENT_ID,
        "client_secret": YOUTUBE_CLIENT_SECRET,
        "refresh_token": YOUTUBE_REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }
    try:
        response = requests.post(token_url, data=data, timeout=30)
        response.raise_for_status()
        token_info = response.json()
        return token_info.get("access_token")
    except Exception as exc:
        logger.error("Failed to refresh YouTube access token: %s", exc)
        return None


def publish_youtube_short(
    video_source: str,
    title: str,
    description: str,
    tags: Optional[list[str]] = None,
) -> dict:
    """
    Publish a video as a YouTube Short.
    video_source: local file path or http(s) URL.
    """
    access_token = get_youtube_access_token()
    if not access_token:
        logger.info("Skipping YouTube Shorts upload: credentials not configured.")
        return {"status": "skipped", "reason": "credentials_not_configured"}

    # Prepare local video file
    temp_download = False
    local_path = None
    if video_source.startswith("http://") or video_source.startswith("https://"):
        temp_download = True
        local_path = Path("temp_yt_upload.mp4")
        logger.info("Downloading remote video for YouTube upload from %s...", video_source)
        res = requests.get(video_source, stream=True, timeout=120)
        res.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    else:
        local_path = Path(video_source)

    if not local_path.exists():
        logger.error("Video file %s not found for YouTube upload.", local_path)
        return {"status": "error", "error": f"File {local_path} not found"}

    # Ensure title contains #Shorts for Shorts shelf discovery
    short_title = title.strip()
    if "#Shorts" not in short_title and "#shorts" not in short_title:
        short_title = f"{short_title} #Shorts"
    short_title = short_title[:100]  # YouTube title limit is 100 characters

    if tags is None:
        tags = ["Shorts", "SRRBazaar", "Sarees", "Jewellery", "Shopping", "Fashion"]

    # 1. Initiate Resumable Upload Session
    metadata = {
        "snippet": {
            "title": short_title,
            "description": description[:5000],
            "tags": tags[:500],
            "categoryId": "22",  # People & Blogs
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    init_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Type": "video/mp4",
    }

    try:
        init_res = requests.post(init_url, headers=headers, json=metadata, timeout=30)
        init_res.raise_for_status()
        upload_url = init_res.headers.get("Location")
        if not upload_url:
            raise RuntimeError("YouTube API did not return a resumable upload Location header.")

        # 2. Upload Video Bytes
        file_size = local_path.stat().st_size
        upload_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "video/mp4",
            "Content-Length": str(file_size),
        }

        with open(local_path, "rb") as video_file:
            upload_res = requests.put(upload_url, headers=upload_headers, data=video_file, timeout=300)
            upload_res.raise_for_status()

        video_data = upload_res.json()
        video_id = video_data.get("id")
        shorts_url = f"https://youtube.com/shorts/{video_id}"
        logger.info("SUCCESS: Published YouTube Short! URL: %s", shorts_url)

        return {
            "status": "published",
            "video_id": video_id,
            "url": shorts_url,
        }

    except Exception as exc:
        logger.error("Failed to publish to YouTube Shorts: %s", exc)
        return {"status": "error", "error": str(exc)}

    finally:
        if temp_download and local_path and local_path.exists():
            try:
                local_path.unlink()
            except Exception:
                pass

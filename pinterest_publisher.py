import os
import logging
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

logger = logging.getLogger("pinterest_publisher")

PINTEREST_API_BASE = "https://api.pinterest.com/v5"
PINTEREST_ACCESS_TOKEN = os.getenv("PINTEREST_ACCESS_TOKEN")

BOARD_CATEGORY_MAP = {
    "necklace": "SRR Bazaar Handcrafted Jewellery",
    "earrings": "SRR Bazaar Handcrafted Jewellery",
    "mangalsutra": "SRR Bazaar Handcrafted Jewellery",
    "saree": "SRR Bazaar Traditional Sarees & Handloom",
    "decor": "SRR Bazaar Pooja Essentials & Sacred Decor",
    "samagri": "SRR Bazaar Pooja Essentials & Sacred Decor",
    "dryfruits": "SRR Bazaar Premium Dry Fruits & Nuts",
    "groceries": "SRR Bazaar Grocery & Daily Staples",
    "snacks": "SRR Bazaar Snacks & Delicacies",
    "cleaning": "SRR Bazaar Home Hygiene & Supplies",
    "electrical": "SRR Bazaar Electrical & Lighting",
    "disposables": "SRR Bazaar Catering & Eco Disposables",
}
DEFAULT_BOARD_NAME = "SRR Bazaar Featured Collections"

# Cache board IDs in memory
_board_cache: dict[str, str] = {}


def get_pinterest_token() -> Optional[str]:
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
    except Exception:
        pass
    return os.getenv("PINTEREST_ACCESS_TOKEN") or PINTEREST_ACCESS_TOKEN


def get_or_create_board(board_name: str, access_token: str) -> Optional[str]:
    """Retrieve existing board ID or create a new board with board_name."""
    if board_name in _board_cache:
        return _board_cache[board_name]

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        # 1. Fetch user's existing boards
        boards_res = requests.get(f"{PINTEREST_API_BASE}/boards?page_size=100", headers=headers, timeout=20)
        if boards_res.status_code == 200:
            for b in boards_res.json().get("items", []):
                _board_cache[b["name"]] = b["id"]
                if b["name"].strip().lower() == board_name.strip().lower():
                    return b["id"]

        # 2. If board does not exist, create it
        create_res = requests.post(
            f"{PINTEREST_API_BASE}/boards",
            headers=headers,
            json={
                "name": board_name,
                "description": f"Curated authentic collections from SRR Bazaar Sujatha Collections (srrbazaar.com).",
                "privacy": "PUBLIC",
            },
            timeout=20,
        )
        if create_res.status_code in (200, 201):
            board_id = create_res.json().get("id")
            _board_cache[board_name] = board_id
            return board_id
        else:
            logger.warning("Could not create board '%s': %s", board_name, create_res.text)
            # Fall back to first available board if creation fails
            items = boards_res.json().get("items", [])
            if items:
                return items[0]["id"]
            return None
    except Exception as exc:
        logger.error("Error managing Pinterest board '%s': %s", board_name, exc)
        return None


def publish_pin(
    title: str,
    description: str,
    product_link: str,
    image_url: str,
    category: Optional[str] = None,
) -> dict:
    """
    Publish a Product Pin to Pinterest with a direct clickable link to srrbazaar.com.
    """
    access_token = get_pinterest_token()
    if not access_token:
        logger.info("Skipping Pinterest Pin creation: PINTEREST_ACCESS_TOKEN not configured.")
        return {"status": "skipped", "reason": "credentials_not_configured"}

    board_name = BOARD_CATEGORY_MAP.get(category, DEFAULT_BOARD_NAME) if category else DEFAULT_BOARD_NAME
    board_id = get_or_create_board(board_name, access_token)

    if not board_id:
        logger.warning("Skipping Pinterest Pin: Could not resolve or create board '%s'.", board_name)
        return {"status": "error", "error": f"Board '{board_name}' not accessible"}

    # Ensure full image URL
    full_image_url = image_url
    if not full_image_url.startswith("http://") and not full_image_url.startswith("https://"):
        full_image_url = f"https://srrbazaar.com/{image_url.lstrip('/')}"

    # Prepare Pin payload
    pin_payload = {
        "title": title[:100],
        "description": description[:500],
        "link": product_link,
        "board_id": board_id,
        "media_source": {
            "source_type": "image_url",
            "url": full_image_url,
        },
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        res = requests.post(f"{PINTEREST_API_BASE}/pins", headers=headers, json=pin_payload, timeout=30)
        data = res.json()
        if res.status_code in (200, 201):
            pin_id = data.get("id")
            pin_url = f"https://www.pinterest.com/pin/{pin_id}/"
            logger.info("SUCCESS: Published Pinterest Pin! ID: %s, URL: %s", pin_id, pin_url)
            return {
                "status": "published",
                "pin_id": pin_id,
                "url": pin_url,
                "board": board_name,
            }
        else:
            logger.warning("Failed to publish Pinterest Pin: %s", data)
            return {"status": "error", "error": str(data)}
    except Exception as exc:
        logger.error("Exception publishing Pinterest Pin: %s", exc)
        return {"status": "error", "error": str(exc)}

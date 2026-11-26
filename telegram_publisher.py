import os
import logging
from pathlib import Path
from typing import Optional
import urllib.parse

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger("telegram_publisher")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")  # e.g. "@srrbazaar" or "-100xxxxxxxxxx"


def get_telegram_config() -> tuple[Optional[str], Optional[str]]:
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
    except Exception:
        pass
    token = os.getenv("TELEGRAM_BOT_TOKEN") or TELEGRAM_BOT_TOKEN
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID") or TELEGRAM_CHANNEL_ID
    return token, chat_id


def publish_telegram_product(
    product_name: str,
    price: str,
    description: str,
    product_id: str | int,
    image_path_or_url: Optional[str] = None,
    video_path: Optional[str] = None,
) -> dict:
    """
    Publish a new product announcement to a Telegram Channel with interactive inline buttons.
    Supports both video reels and high-res photos.
    """
    token, chat_id = get_telegram_config()
    if not token or not chat_id:
        logger.info("Skipping Telegram announcement: TELEGRAM_BOT_TOKEN or TELEGRAM_CHANNEL_ID not configured.")
        return {"status": "skipped", "reason": "credentials_not_configured"}

    clean_name = product_name.strip() if product_name else "Exclusive Collection"
    price_str = price.strip() if price else ""
    if price_str and not price_str.startswith("₹"):
        price_str = f"₹{price_str}"

    prod_url = f"https://srrbazaar.com/p/{product_id}.html"
    wa_order_text = urllib.parse.quote(f"Hi SRR Bazaar, I would like to order *{clean_name}* ({price_str}). Link: {prod_url}")
    wa_order_url = f"https://wa.me/918185012453?text={wa_order_text}"

    # Rich Telegram HTML Caption
    caption = (
        f"✨ <b>{clean_name}</b> — <i>SRR Bazaar Sujatha Collections</i> ✨\n\n"
        f"🏷️ <b>Launch Price:</b> <code>{price_str}</code> ONLY\n"
        f"🚚 <b>FREE Express Shipping Pan-India</b>\n"
        f"📦 <b>Cash on Delivery (COD) Available</b>\n"
        f"💯 <b>100% Genuine Quality Guaranteed</b>\n\n"
        f"📝 <b>Description:</b>\n{description.strip()[:400]}\n\n"
        f"📲 <b>Direct Helpline:</b> +91 8185012453 / +91 9948633303 / +91 7013416296\n\n"
        f"#SRRBazaar #SujathaCollections #OnlineShoppingIndia #COD #NewArrivals"
    )

    # Inline Keyboard with Action Buttons
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🛍️ Buy Online & Pay (Direct)", "url": prod_url},
                {"text": "💬 Order via WhatsApp", "url": wa_order_url},
            ],
            [
                {"text": "🌐 Explore All Deals (srrbazaar.com)", "url": "https://srrbazaar.com"},
            ]
        ]
    }

    base_api = f"https://api.telegram.org/bot{token}"

    try:
        # 1. If matching video reel exists, post as sendVideo
        if video_path and Path(video_path).exists():
            video_file_path = Path(video_path)
            logger.info("Publishing video reel to Telegram channel %s...", chat_id)
            url = f"{base_api}/sendVideo"
            with open(video_file_path, "rb") as vf:
                files = {"video": vf}
                data = {
                    "chat_id": chat_id,
                    "caption": caption,
                    "parse_mode": "HTML",
                    "supports_streaming": "true",
                    "reply_markup": requests.compat.json.dumps(reply_markup),
                }
                res = requests.post(url, data=data, files=files, timeout=120)
                res_data = res.json()
                if res_data.get("ok"):
                    msg_id = res_data["result"]["message_id"]
                    logger.info("SUCCESS: Video reel published to Telegram! Msg ID: %s", msg_id)
                    return {"status": "published", "type": "video", "message_id": msg_id}
                else:
                    logger.warning("Telegram sendVideo failed: %s. Falling back to photo.", res_data)

        # 2. Fallback: post as sendPhoto
        if image_path_or_url:
            img_path = Path(image_path_or_url)
            if img_path.exists():
                url = f"{base_api}/sendPhoto"
                with open(img_path, "rb") as pf:
                    files = {"photo": pf}
                    data = {
                        "chat_id": chat_id,
                        "caption": caption,
                        "parse_mode": "HTML",
                        "reply_markup": requests.compat.json.dumps(reply_markup),
                    }
                    res = requests.post(url, data=data, files=files, timeout=60)
                    res_data = res.json()
                    if res_data.get("ok"):
                        msg_id = res_data["result"]["message_id"]
                        logger.info("SUCCESS: Product photo published to Telegram! Msg ID: %s", msg_id)
                        return {"status": "published", "type": "photo", "message_id": msg_id}
                    else:
                        logger.warning("Telegram sendPhoto file failed: %s", res_data)
            elif image_path_or_url.startswith("http://") or image_path_or_url.startswith("https://"):
                url = f"{base_api}/sendPhoto"
                data = {
                    "chat_id": chat_id,
                    "photo": image_path_or_url,
                    "caption": caption,
                    "parse_mode": "HTML",
                    "reply_markup": requests.compat.json.dumps(reply_markup),
                }
                res = requests.post(url, json=data, timeout=30)
                res_data = res.json()
                if res_data.get("ok"):
                    msg_id = res_data["result"]["message_id"]
                    logger.info("SUCCESS: Product photo URL published to Telegram! Msg ID: %s", msg_id)
                    return {"status": "published", "type": "photo", "message_id": msg_id}

        # 3. Text fallback if no media found
        url = f"{base_api}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": caption,
            "parse_mode": "HTML",
            "reply_markup": reply_markup,
        }
        res = requests.post(url, json=data, timeout=30)
        res_data = res.json()
        if res_data.get("ok"):
            msg_id = res_data["result"]["message_id"]
            return {"status": "published", "type": "text", "message_id": msg_id}
        else:
            return {"status": "error", "error": str(res_data)}

    except Exception as exc:
        logger.error("Exception publishing to Telegram: %s", exc)
        return {"status": "error", "error": str(exc)}

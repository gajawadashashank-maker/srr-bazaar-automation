import os
import logging
from pathlib import Path
from typing import Optional
import urllib.parse
import urllib.request
import json

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
        f"📌 <b>Pinterest:</b> https://in.pinterest.com/sujathagajawada/\n"
        f"✈️ <b>Telegram Channel:</b> https://t.me/srrbazaardeals\n"
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
                {"text": "🌐 Visit Website", "url": "https://srrbazaar.com"},
                {"text": "📌 Pinterest", "url": "https://in.pinterest.com/sujathagajawada/"},
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


def send_merchant_order_alert(order_data: dict) -> dict:
    """
    Sends an instant private alert to the merchant on Telegram when a customer places an order.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
    except Exception:
        pass

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID") or "1478699141"
    if not token or not admin_id:
        return {"status": "skipped", "reason": "admin_credentials_not_configured"}

    order_id = order_data.get("orderId", "N/A")
    cust = order_data.get("customer", {})
    cust_name = cust.get("name", "Valued Customer")
    cust_phone = cust.get("phone", "N/A")
    cust_addr = f"{cust.get('address', '')}, {cust.get('city', '')}, {cust.get('state', '')} - {cust.get('pincode', '')}"
    
    total = order_data.get("total", 0)
    pay_mode = order_data.get("paymentMethod", "Cash on Delivery")
    ref = order_data.get("refNumber", "")
    adv = order_data.get("advancePaid", 0)
    cod_bal = order_data.get("codBalance", total)

    items = order_data.get("items", [])
    item_lines = []
    for idx, it in enumerate(items, 1):
        it_title = it.get("title") or it.get("name", "Product")
        it_qty = it.get("qty", 1)
        it_price = it.get("price", 0)
        if it.get("isFreeGift"):
            item_lines.append(f"  {idx}. 🎁 <b>FREE GIFT:</b> {it_title} (Qty: {it_qty})")
        else:
            item_lines.append(f"  {idx}. 🛍️ <b>{it_title}</b> x {it_qty} = ₹{it_price * it_qty}")
    items_text = "\n".join(item_lines) if item_lines else "  No item details"

    free_gift_note = ""
    if order_data.get("freeGift"):
        free_gift_note = f"\n🎡 <b>Festive Wheel Winner Prize:</b> {order_data.get('freeGift')}"

    text = (
        f"🚨 <b>NEW ORDER RECEIVED!</b> 🛍️\n\n"
        f"📋 <b>Order ID:</b> <code>{order_id}</code>\n"
        f"💰 <b>Total Amount:</b> <b>₹{total}</b>\n"
        f"💳 <b>Payment Mode:</b> {pay_mode}\n"
    )
    if adv > 0:
        text += f"⚡ <b>Advance Token Received:</b> ₹{adv} (UTR: <code>{ref}</code>)\n"
        text += f"💵 <b>COD Balance on Delivery:</b> ₹{cod_bal}\n"
    elif ref:
        text += f"🔖 <b>UTR / Payment Ref:</b> <code>{ref}</code>\n"

    text += (
        f"\n📦 <b>Order Items:</b>\n{items_text}{free_gift_note}\n\n"
        f"👤 <b>Customer Details:</b>\n"
        f"• <b>Name:</b> {cust_name}\n"
        f"• <b>Phone:</b> <code>{cust_phone}</code>\n"
        f"• <b>Delivery Address:</b>\n  {cust_addr}\n\n"
        f"⚡ <i>Action required: Pack items and dispatch via The Professional Couriers (Armoor Hub).</i>"
    )

    clean_phone = cust_phone.replace("+", "").replace(" ", "").replace("-", "")
    if not clean_phone.startswith("91") and len(clean_phone) == 10:
        clean_phone = f"91{clean_phone}"

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "💬 Message Customer on WhatsApp", "url": f"https://wa.me/{clean_phone}?text=Namaste%20{urllib.parse.quote(cust_name)},%20thank%20you%20for%20ordering%20from%20SRR%20Bazaar%20(Order%20{order_id})!%20Your%20order%20is%20being%20packed."},
            ],
            [
                {"text": "🛍️ View Storefront", "url": "https://srrbazaar.com"},
                {"text": "✈️ Telegram Deals", "url": "https://t.me/srrbazaardeals"}
            ]
        ]
    }

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": admin_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": reply_markup
    }

    try:
        if requests:
            res = requests.post(url, json=payload, timeout=15)
            return res.json()
        else:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            resp = urllib.request.urlopen(req, timeout=15)
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.error("Failed to send merchant order alert: %s", e)
        return {"status": "error", "error": str(e)}


def send_merchant_spin_alert(phone: str, prize_label: str) -> dict:
    """
    Sends an instant private alert when someone wins a prize on the Spin & Win wheel.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
    except Exception:
        pass

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID") or "1478699141"
    if not token or not admin_id:
        return {"status": "skipped", "reason": "admin_credentials_not_configured"}

    text = (
        f"🎡 <b>FESTIVE WHEEL WINNER!</b> 🎁\n\n"
        f"👤 <b>Player Phone:</b> <code>{phone}</code>\n"
        f"🏆 <b>Prize Won:</b> <b>{prize_label}</b>\n"
        f"⏰ <b>Status:</b> Active in Cart / Wallet (Valid 24 Hours)\n"
    )

    clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    if not clean_phone.startswith("91") and len(clean_phone) == 10:
        clean_phone = f"91{clean_phone}"

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "💬 WhatsApp Winner", "url": f"https://wa.me/{clean_phone}?text=Congratulations!%20You%20won%20{urllib.parse.quote(prize_label)}%20on%20the%20SRR%20Bazaar%20Festive%20Wheel!"}
            ]
        ]
    }

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": admin_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": reply_markup
    }

    try:
        if requests:
            res = requests.post(url, json=payload, timeout=15)
            return res.json()
        else:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            resp = urllib.request.urlopen(req, timeout=15)
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.error("Failed to send merchant spin alert: %s", e)
        return {"status": "error", "error": str(e)}


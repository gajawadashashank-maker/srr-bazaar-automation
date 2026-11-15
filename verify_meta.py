
import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
INSTAGRAM_ID = os.getenv("META_INSTAGRAM_ACCOUNT_ID")

if not ACCESS_TOKEN or not INSTAGRAM_ID:
    raise RuntimeError("Missing Meta credentials in .env")

url = f"https://graph.facebook.com/v27.0/{INSTAGRAM_ID}"

params = {
    "fields": "id,username",
    "access_token": ACCESS_TOKEN
}

try:
    response = requests.get(url, params=params, timeout=30)
    data = response.json()

    if response.ok and "username" in data:
        print("META API CONNECTION SUCCESSFUL")
        print("Instagram ID:", data["id"])
        print("Instagram username:", data["username"])
    else:
        error = data.get("error", {})
        print("META API VERIFICATION FAILED")
        print("HTTP status:", response.status_code)
        print("Error:", error.get("message", "Unknown error"))
        print("Error code:", error.get("code", "N/A"))

except requests.RequestException as exc:
    print("Connection error:", str(exc))

"""
One-time setup script to authorize YouTube Shorts uploads for your channel.
Run: python setup_youtube_token.py
"""
import os
import urllib.parse
import webbrowser
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
REDIRECT_URI = "http://localhost:8088/"


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        code = params.get("code", [None])[0]

        if code:
            self.server.auth_code = code
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>Authorization Successful!</h1><p>You can close this tab and return to your terminal.</p>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Failed to receive auth code.")

    def log_message(self, format, *args):
        return  # Suppress default server logs


def main():
    global CLIENT_ID, CLIENT_SECRET

    print("\n" + "=" * 60)
    print("SRR BAZAAR — YOUTUBE SHORTS AUTOMATION SETUP")
    print("=" * 60)

    if not CLIENT_ID or not CLIENT_SECRET:
        print("\nTo connect your YouTube channel, you need a free Google Cloud OAuth Client ID.")
        print("1. Go to: https://console.cloud.google.com/apis/credentials")
        print("2. Create an OAuth 2.0 Client ID (Web Application or Desktop App)")
        print("   - Redirect URI: http://localhost:8088/")
        CLIENT_ID = input("\nEnter your Google Client ID: ").strip()
        CLIENT_SECRET = input("Enter your Google Client Secret: ").strip()

    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urllib.parse.urlencode({
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
        })
    )

    print("\nOpening your browser to authorize your YouTube channel...")
    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", 8088), OAuthCallbackHandler)
    server.auth_code = None

    print("Waiting for you to sign in with your Google Account...")
    while not server.auth_code:
        server.handle_request()

    code = server.auth_code
    print("Received authorization code! Exchanging for permanent refresh token...")

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }

    res = requests.post(token_url, data=data)
    token_json = res.json()
    refresh_token = token_json.get("refresh_token")

    if not refresh_token:
        print("Error exchanging token:", token_json)
        return

    print("\nSUCCESS! Permanent YouTube Refresh Token acquired.")
    print("Writing credentials to your .env file...")

    env_lines = []
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            env_lines = f.readlines()

    keys_to_set = {
        "YOUTUBE_CLIENT_ID": CLIENT_ID,
        "YOUTUBE_CLIENT_SECRET": CLIENT_SECRET,
        "YOUTUBE_REFRESH_TOKEN": refresh_token,
    }

    new_lines = [line for line in env_lines if not any(line.startswith(k + "=") for k in keys_to_set)]
    for k, v in keys_to_set.items():
        new_lines.append(f"{k}={v}\n")

    with open(".env", "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print("\nSaved to .env! YouTube Shorts will now automatically upload alongside Instagram Reels!")


if __name__ == "__main__":
    main()

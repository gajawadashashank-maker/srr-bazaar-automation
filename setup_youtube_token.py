"""
One-time setup script to authorize YouTube Shorts uploads for your channel.
100% Standalone: Uses only Python standard library (no pip packages needed).
"""
import os
import json
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
REDIRECT_URI = "http://localhost:8088/"


def load_env_vars():
    env = {}
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip("'\"")
    return env


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
            self.wfile.write(b"<h1>Authorization Successful!</h1><p>You can close this browser tab now and return to your terminal.</p>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Failed to receive auth code.")

    def log_message(self, format, *args):
        return  # Suppress default server logs


def main():
    env = load_env_vars()
    client_id = env.get("YOUTUBE_CLIENT_ID")
    client_secret = env.get("YOUTUBE_CLIENT_SECRET")

    print("\n" + "=" * 60)
    print("SRR BAZAAR — YOUTUBE SHORTS AUTOMATION SETUP")
    print("=" * 60)

    if not client_id or not client_secret:
        print("\nTo connect your YouTube channel, you need a Google Cloud OAuth Client ID:")
        print("1. Go to: https://console.cloud.google.com/apis/credentials")
        print("2. Create an OAuth 2.0 Client ID (Web Application)")
        print("   - Authorized redirect URI: http://localhost:8088/")
        client_id = input("\nEnter your Google Client ID: ").strip()
        client_secret = input("Enter your Google Client Secret: ").strip()

    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urllib.parse.urlencode({
            "client_id": client_id,
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
    payload = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }).encode("utf-8")

    req = urllib.request.Request(token_url, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req) as resp:
            token_json = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print("Error exchanging token:", e)
        return

    refresh_token = token_json.get("refresh_token")
    if not refresh_token:
        print("Error: No refresh token returned. Response was:", token_json)
        return

    print("\nSUCCESS! Permanent YouTube Refresh Token acquired.")
    print("Writing credentials to your .env file...")

    env_lines = []
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            env_lines = f.readlines()

    keys_to_set = {
        "YOUTUBE_CLIENT_ID": client_id,
        "YOUTUBE_CLIENT_SECRET": client_secret,
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

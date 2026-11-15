# Cloudflare Worker: WhatsApp to GitHub Actions Webhook Bridge

This Cloudflare Worker provides a $0/month serverless bridge between Meta's WhatsApp Cloud API and GitHub Actions.

## How it works

1. **Meta Webhook Verification (`GET /`)**:
   - Meta queries your Worker endpoint to verify the webhook.
   - The worker verifies `hub.verify_token` against `WHATSAPP_VERIFY_TOKEN` and echoes `hub.challenge`.

2. **Incoming WhatsApp Message (`POST /`)**:
   - Meta sends an image message to your Worker.
   - The worker validates the sender and message type (`image`).
   - Immediately returns `200 OK` to Meta (preventing timeouts).
   - Simultaneously calls the GitHub API (`repository_dispatch`) to spin up an Ubuntu runner on GitHub Actions.
   - GitHub Actions downloads the image, generates 4 reels, uploads the selected reel to Cloudinary, and publishes it to Instagram.

---

## Setup Instructions (2 Minutes)

### Option A: Using the Cloudflare Dashboard (No Terminal Required)

1. Sign in to [Cloudflare Dashboard](https://dash.cloudflare.com/) (Free plan).
2. Go to **Compute (Workers) > Workers & Pages** -> Click **Create application** -> **Create Worker**.
3. Name it `srr-bazaar-webhook` and click **Deploy**.
4. Click **Edit code**, delete existing sample code, and paste the contents of `worker.js`.
5. Click **Deploy**.
6. Go to the worker's **Settings > Variables and Secrets**:
   - Add Plain text variables:
     - `GITHUB_OWNER`: `gajawadashashank-maker`
     - `GITHUB_REPO`: `srr-bazaar-automation`
     - `WHATSAPP_PHONE_NUMBER_ID`: `872753362597934`
     - `ALLOWED_SENDERS`: `919948633303,918185012453`
   - Add Secrets (Encrypted):
     - `WHATSAPP_VERIFY_TOKEN`: `SRR_Bazaar_Webhook_2026`
     - `GITHUB_PAT`: Your GitHub Personal Access Token (with `repo` or `actions:write` permission)
     - `META_APP_SECRET`: (Optional) Your Meta App Secret
7. Copy your Worker URL (e.g., `https://srr-bazaar-webhook.<your-subdomain>.workers.dev`).
8. In Meta Developer Portal:
   - Paste the Worker URL into your WhatsApp Configuration Webhook URL.
   - Enter your Verify Token (`SRR_Bazaar_Webhook_2026`).
   - Click **Verify and Save**, then subscribe to `messages`.

---

### Option B: Using Wrangler CLI

1. Open a terminal in `cloudflare-worker/`:
   ```bash
   npx wrangler login
   npx wrangler secret put GITHUB_PAT
   npx wrangler secret put WHATSAPP_VERIFY_TOKEN
   npx wrangler secret put META_APP_SECRET
   npx wrangler deploy
   ```

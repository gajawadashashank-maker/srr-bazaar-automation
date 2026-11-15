# SRR Bazaar Automation (WhatsApp to Instagram Reel Publisher)

Zero-cost ($0/month) cloud automation that receives product images and captions via WhatsApp Cloud API, generates 4 high-quality 9:16 Instagram Reels using FFmpeg, uploads to Cloudinary CDN, and automatically publishes them to Instagram Reels via Meta Graph API.

**Your PC can be turned completely OFF.** All processing runs on free cloud runners!

---

## 🏗️ Architecture

```
[ WhatsApp User ] 
       │ (Sends photo + caption)
       ▼
[ WhatsApp Cloud API ]
       │ (Webhook POST)
       ▼
[ Cloudflare Worker ]  <-- FREE (100,000 requests/day)
  • Immediate 200 OK to Meta
  • Validates sender & extracts media ID
  • Calls GitHub repository_dispatch API
       │
       ▼
[ GitHub Actions Ubuntu Runner ] <-- FREE (2,000 min/mo private / unlimited public)
  • Temporary Ubuntu VM spins up
  • Downloads original photo from WhatsApp API
  • Generates all 4 reel themes via FFmpeg
  • Randomly picks 1 theme for publication
  • Uploads selected reel to Cloudinary CDN
  • Publishes Reel to Instagram via Meta Graph API
  • (Optional) Sends WhatsApp confirmation to sender
  • Stores all 4 reels as downloadable workflow artifacts
```

---

## 🚀 Setup Guide

### Step 1: Add GitHub Secrets to your Repository
Go to your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret Name | Value Description |
|---|---|
| `CLOUDINARY_CLOUD_NAME` | Your Cloudinary Cloud Name |
| `CLOUDINARY_API_KEY` | Your Cloudinary API Key |
| `CLOUDINARY_API_SECRET` | Your Cloudinary API Secret |
| `META_APP_ID` | Your Meta Developer App ID |
| `META_CONFIG_ID` | Your Meta Config ID |
| `META_SYSTEM_USER_ID` | Your System User ID |
| `META_INSTAGRAM_ACCOUNT_ID` | Your Instagram Business Account ID |
| `META_ACCESS_TOKEN` | Long-lived Meta System User Access Token |
| `META_APP_SECRET` | Your Meta App Secret |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp Business Phone Number ID |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp Cloud API Access Token |
| `WHATSAPP_AUTO_PUBLISH` | `true` (or `false` to generate without posting) |

---

### Step 2: Create a GitHub Personal Access Token (PAT)
The Cloudflare Worker needs permission to trigger GitHub Actions:
1. In GitHub, click your profile photo → **Settings** → **Developer Settings** → **Personal access tokens** → **Tokens (classic)**.
2. Click **Generate new token (classic)**.
3. Note: `Cloudflare Worker Trigger`.
4. Check the **`repo`** scope (or `workflow`).
5. Click **Generate token** and copy the token value (`ghp_...`).

---

### Step 3: Deploy the Cloudflare Worker
1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/) (free account).
2. Go to **Compute (Workers) → Workers & Pages** → click **Create application** → **Create Worker**.
3. Name it `srr-bazaar-webhook` and click **Deploy**.
4. Click **Edit code**, delete default template, and copy-paste the code from [`cloudflare-worker/worker.js`](cloudflare-worker/worker.js).
5. Click **Deploy**.
6. Under your Worker's **Settings → Variables and Secrets**:
   - **Environment Variables**:
     - `GITHUB_OWNER`: `gajawadashashank-maker`
     - `GITHUB_REPO`: `srr-bazaar-automation`
     - `WHATSAPP_PHONE_NUMBER_ID`: `872753362597934`
     - `ALLOWED_SENDERS`: `919948633303,918185012453`
   - **Secrets (Encrypted)**:
     - `GITHUB_PAT`: `<Your Personal Access Token from Step 2>`
     - `WHATSAPP_VERIFY_TOKEN`: `SRR_Bazaar_Webhook_2026`
     - `META_APP_SECRET`: `<Your Meta App Secret>`
7. Copy your Worker URL: `https://srr-bazaar-webhook.<subdomain>.workers.dev`.

---

### Step 4: Configure Meta WhatsApp Webhook
1. Go to [developers.facebook.com](https://developers.facebook.com) → Your App → **WhatsApp → Configuration**.
2. In the **Webhook** section, click **Edit**:
   - **Callback URL**: `https://srr-bazaar-webhook.<subdomain>.workers.dev`
   - **Verify Token**: `SRR_Bazaar_Webhook_2026`
3. Click **Verify and Save**.
4. Under **Webhook Fields**, click **Manage** and subscribe to **`messages`**.

---

## 🧪 Testing

### Manual Cloud Test (GitHub Actions)
You can test the GitHub runner anytime without sending a WhatsApp message:
1. Go to your repo on GitHub → **Actions** tab.
2. Select **Generate & Publish Instagram Reel**.
3. Click **Run workflow** and enter test caption and options.
4. Watch the Ubuntu runner build the reels and publish to Instagram in ~60 seconds!

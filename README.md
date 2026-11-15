# SRR Bazaar Automation — WhatsApp to Instagram Reels

Send a product image and caption to the connected WhatsApp Business number. GitHub Actions generates all four 9:16 Reel themes, randomly selects one, uploads it to Cloudinary, and publishes it to Instagram.

**Your Windows PC does not need to stay online.** Standard GitHub-hosted runners are free for public repositories. Artifact storage and other account-level limits still apply.

## Architecture

1. WhatsApp Cloud API sends a webhook to the Cloudflare Worker.
2. The Worker verifies Meta's HMAC signature, checks the business phone number and sender allowlist, and deduplicates by WhatsApp message ID using Workers KV.
3. The Worker triggers this repository's repository_dispatch event: whatsapp_submission.
4. GitHub Actions downloads the image from Meta, runs FFmpeg/Pillow, creates four themes, randomly selects one, uploads it to Cloudinary, and publishes through the Instagram Graph API.
5. The workflow uploads generated files as a short-lived Actions artifact.

## Four Reel themes

- luxury_gold_black
- elegant_white_gold
- pink_modern
- minimal_premium

Reels are rendered at 1080 × 1920, 30 fps, and 8 seconds. The price parser supports captions such as "Only 1999 free shipping", "Just ₹1,999", "Price: 1999", "₹1,999", and "@1999".

## 1. Add GitHub Actions secrets

Open Settings → Secrets and variables → Actions → New repository secret and add:

| Secret | Value |
|---|---|
| CLOUDINARY_CLOUD_NAME | Cloudinary cloud name |
| CLOUDINARY_API_KEY | Cloudinary API key |
| CLOUDINARY_API_SECRET | Cloudinary API secret |
| META_INSTAGRAM_ACCOUNT_ID | Instagram professional account ID |
| META_ACCESS_TOKEN | Meta access token with Instagram publishing permissions |
| META_API_VERSION | v27.0 |
| WHATSAPP_PHONE_NUMBER_ID | Connected WhatsApp Business Phone Number ID |
| WHATSAPP_ACCESS_TOKEN | WhatsApp Cloud API access token |
| WHATSAPP_API_VERSION | v27.0 |
| WHATSAPP_AUTO_PUBLISH | true |

Never commit real tokens, .env files, or credentials. The .env.example file contains placeholders only.

## 2. Create the GitHub dispatch token

Create a fine-grained personal access token restricted to this repository:

- Repository access: Only select repositories → srr-bazaar-automation
- Repository permissions: Contents → Read and write

Save it in Cloudflare as the encrypted secret GITHUB_PAT. Do not paste it into source files, GitHub issues, or chat. The GitHub repository dispatch endpoint requires Contents: write for fine-grained tokens.

## 3. Deploy the Cloudflare Worker

Open Cloudflare Dashboard → Workers & Pages:

1. Create or open the Worker named srr-bazaar-whatsapp-webhook.
2. Replace its code with cloudflare-worker/worker.js, then deploy.
3. Open Storage & Databases → Workers KV and create a namespace, for example SRR_BAZAAR_SEEN_MESSAGES.
4. Open the Worker Settings → Bindings and add a KV namespace binding:
   - Variable name: SEEN_MESSAGES
   - Namespace: SRR_BAZAAR_SEEN_MESSAGES
5. Under Settings → Variables and Secrets, add these plain-text variables:
   - GITHUB_OWNER = gajawadashashank-maker
   - GITHUB_REPO = srr-bazaar-automation
   - WHATSAPP_PHONE_NUMBER_ID = your connected WhatsApp Business Phone Number ID
   - ALLOWED_SENDERS = approved numbers with country code, comma-separated, for example 919948633303,918185012453
6. Add these as encrypted secrets:
   - GITHUB_PAT = fine-grained PAT from Step 2
   - WHATSAPP_VERIFY_TOKEN = your webhook verify token
   - META_APP_SECRET = Meta App Secret (required for signature verification)

The Wrangler config is cloudflare-worker/wrangler.toml. For CLI deployment, add the KV namespace ID there before running npx wrangler deploy. The dashboard binding is sufficient when using the online editor.

After deployment, open https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev/health. It should return a JSON status of ok.

Cloudflare's current Workers Free limits include 100,000 requests/day. Workers KV Free includes 100,000 reads/day, 1,000 writes/day, and 1 GB storage. The Worker uses a small number of operations per message.

## 4. Connect the Meta webhook

In Meta for Developers → your app → WhatsApp → Configuration:

- Callback URL: https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev/
- Verify token: the same value as Cloudflare's WHATSAPP_VERIFY_TOKEN
- Verify and save.
- Subscribe to the messages webhook field.

The Worker validates X-Hub-Signature-256. Keep META_APP_SECRET configured; signature checking is mandatory.

## 5. Send a product image

Send or forward one product image directly to the connected WhatsApp Business number from an approved sender. Include a caption such as:

    Premium Pure Jadau Necklace Set
    Only 1999 free shipping

Or:

    Product: Premium Necklace Set
    Description: Changeable lockets, premium finish
    Price: ₹1,999

The title and detected price are printed on the poster and included in the Instagram caption. One image message creates all four variants and publishes one random selection.

## Manual test

Open Actions → Generate & Publish Instagram Reel → Run workflow. Use an image URL or WhatsApp media ID and enter a caption. Set auto-publish to false to test generation without posting.

## Public-repository visibility

This repository is public as requested. Source code, workflow files, Actions logs, and uploaded workflow artifacts can be visible to people who can read the repository. Product photos and generated videos may therefore be downloadable from workflow runs. The workflow reduces log detail, but do not send confidential images or personal information through this public workflow.

Only publish background audio that you have permission to use. The audio file currently in music/ is also part of this public repository.

## Operational notes

- No AWS VM, ngrok tunnel, always-on Python server, or R2 bucket is required.
- WhatsApp group content is not received automatically; forward a product image directly to the connected business number.
- If a dispatch fails, the Worker returns an error so Meta can retry. Successfully dispatched message IDs are kept in KV for seven days.
- Standard GitHub-hosted runner compute is free for this public repository; artifact storage and other service limits are not unlimited.

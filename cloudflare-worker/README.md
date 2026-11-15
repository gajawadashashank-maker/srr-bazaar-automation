# Cloudflare Worker — WhatsApp to GitHub Actions

This Worker receives Meta WhatsApp webhooks, verifies their signature, checks the configured business number and sender allowlist, deduplicates messages with Workers KV, and triggers the existing GitHub Actions workflow.

## 1. Deploy the Worker

1. Open Cloudflare Dashboard → Workers & Pages.
2. Create a Worker named srr-bazaar-whatsapp-webhook (or open the existing Worker).
3. Replace the online editor code with the contents of worker.js in this folder.
4. Deploy.

## 2. Create and bind Workers KV

1. Open Storage & Databases → Workers KV.
2. Create a namespace, for example SRR_BAZAAR_SEEN_MESSAGES.
3. Open the Worker → Settings → Bindings → Add binding → KV namespace.
4. Set the variable name to exactly SEEN_MESSAGES and select the namespace you created.
5. Save and deploy the Worker again.

The Worker stores a message-ID marker for seven days after GitHub accepts a dispatch. If KV is not bound, POST requests intentionally fail rather than process images without deduplication.

## 3. Configure variables and encrypted secrets

Worker Settings → Variables and Secrets:

Plain-text variables:
- GITHUB_OWNER = gajawadashashank-maker
- GITHUB_REPO = srr-bazaar-automation
- WHATSAPP_PHONE_NUMBER_ID = your WhatsApp Business Phone Number ID
- ALLOWED_SENDERS = approved sender numbers with country code, comma-separated

Encrypted secrets:
- GITHUB_PAT = fine-grained personal access token for this repository
- WHATSAPP_VERIFY_TOKEN = your chosen Meta webhook verification token
- META_APP_SECRET = Meta App Secret

Create the GitHub PAT with repository access restricted to srr-bazaar-automation and repository permission Contents → Read and write. That is the permission required by GitHub's Create a repository dispatch event endpoint. Do not use a broad token or commit it to the repository.

The Meta App Secret is mandatory. The Worker checks the X-Hub-Signature-256 header and rejects invalid webhook signatures.

## 4. Configure the Meta WhatsApp webhook

In Meta for Developers → your app → WhatsApp → Configuration:

- Callback URL: your deployed Worker URL, ending in /
- Verify token: exactly the same value configured as WHATSAPP_VERIFY_TOKEN
- Verify and save.
- Subscribe to messages.

A health endpoint is available at /health and should return JSON with status ok.

## 5. Workflow event contract

The Worker dispatches event type whatsapp_submission. Its client payload contains:

- media_id
- caption
- sender
- message_id
- phone_number_id

The repository workflow already listens for this event and passes the values to process_job.py.

## Troubleshooting

- HTTP 401 from the Worker: check Meta's app secret and signature configuration.
- HTTP 503 from the Worker: check the SEEN_MESSAGES KV binding, phone number ID, and sender allowlist.
- HTTP 502 from the Worker: check the GitHub PAT and its Contents: Read and write permission, then inspect the GitHub Actions run.
- No GitHub run: confirm the workflow is enabled under the repository Actions tab and that the Worker dispatch event is whatsapp_submission.

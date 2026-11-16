# Credential setup template — SRR Bazaar Automation

This file is a copy guide. Values beginning with REPLACE_ME are placeholders only. They are not working credentials. Replace them in GitHub or Cloudflare settings; never commit real values into this repository.

## A. GitHub Actions — Repository secrets

Open: Settings → Secrets and variables → Actions → Repository secrets → New repository secret.

Create these names exactly. A temporary placeholder value can be used while preparing the page, but the workflow will not run successfully until you replace it with the real credential.

| Secret name | Placeholder value | Where to obtain the real value |
|---|---|---|
| CLOUDINARY_CLOUD_NAME | REPLACE_ME_CLOUDINARY_CLOUD_NAME | Cloudinary dashboard → product environment |
| CLOUDINARY_API_KEY | REPLACE_ME_CLOUDINARY_API_KEY | Cloudinary dashboard → API keys |
| CLOUDINARY_API_SECRET | REPLACE_ME_CLOUDINARY_API_SECRET | Cloudinary dashboard → API keys |
| META_INSTAGRAM_ACCOUNT_ID | REPLACE_ME_INSTAGRAM_PROFESSIONAL_ACCOUNT_ID | Meta Graph API / Instagram professional account ID |
| META_ACCESS_TOKEN | REPLACE_ME_META_INSTAGRAM_ACCESS_TOKEN | Meta app/system user token with Instagram publishing permissions |
| META_API_VERSION | v27.0 | Graph API version configured for this app |
| WHATSAPP_PHONE_NUMBER_ID | REPLACE_ME_WHATSAPP_PHONE_NUMBER_ID | Meta WhatsApp → API Setup |
| WHATSAPP_ACCESS_TOKEN | REPLACE_ME_WHATSAPP_CLOUD_API_TOKEN | Meta WhatsApp Cloud API token |
| WHATSAPP_API_VERSION | v27.0 | WhatsApp Graph API version configured for this app |
| WHATSAPP_AUTO_PUBLISH | true | Set to false to generate without publishing |

META_APP_SECRET is used by the Cloudflare Worker for webhook HMAC verification. It does not need to be exposed to the GitHub Actions runner.

## B. GitHub Actions — Repository variable

Open: Settings → Secrets and variables → Actions → Variables → New repository variable.

| Variable name | Value |
|---|---|
| ALLOWED_SENDERS | REPLACE_ME_WITH_APPROVED_SENDERS_E164_COMMA_SEPARATED |

Example format only: 91XXXXXXXXXX,91YYYYYYYYYY. Use the actual approved sender numbers with country code.

## C. Cloudflare Worker — Plain-text variables

Open: Cloudflare Dashboard → Workers & Pages → your Worker → Settings → Variables and Secrets.

| Variable name | Value |
|---|---|
| GITHUB_OWNER | gajawadashashank-maker |
| GITHUB_REPO | srr-bazaar-automation |
| WHATSAPP_PHONE_NUMBER_ID | REPLACE_ME_WHATSAPP_PHONE_NUMBER_ID |
| ALLOWED_SENDERS | REPLACE_ME_WITH_APPROVED_SENDERS_E164_COMMA_SEPARATED |

## D. Cloudflare Worker — Encrypted secrets

Create these as encrypted secrets, not plain-text variables.

| Secret name | Placeholder value | Purpose |
|---|---|---|
| GITHUB_PAT | REPLACE_ME_FINE_GRAINED_GITHUB_PAT | Repository dispatch; restrict to this repo with Contents: Read and write |
| WHATSAPP_VERIFY_TOKEN | REPLACE_ME_META_WEBHOOK_VERIFY_TOKEN | Must exactly match the Verify Token entered in Meta |
| META_APP_SECRET | REPLACE_ME_META_APP_SECRET | Verifies Meta X-Hub-Signature-256 webhook signatures |

## E. Required Cloudflare KV binding

Create a Workers KV namespace, then bind it to the Worker:

| Setting | Value |
|---|---|
| Binding type | KV namespace |
| Variable name | SEEN_MESSAGES |
| Namespace | Select the namespace you created |

The Worker intentionally rejects POST requests if this binding is missing. It retains a successfully dispatched WhatsApp message ID for seven days to reduce duplicate runs.

## F. Security and activation checklist

- [ ] Replace every REPLACE_ME value with a real value before testing.
- [ ] Do not put credentials in source code, README files, Issues, or chat.
- [ ] Keep the repository public only if source files, Actions logs, generated artifacts, and product media may be visible to others.
- [ ] Deploy the Cloudflare Worker after adding its KV binding and encrypted secrets.
- [ ] Set the Meta WhatsApp webhook callback URL to the deployed Worker URL and subscribe to messages.
- [ ] Send one non-confidential test product image directly to the WhatsApp Business number from an approved sender.
- [ ] Confirm one GitHub Actions run completes and the Reel is published as expected.

Important: This is a configuration checklist. GitHub Actions secret values must be created or overwritten in repository Settings. The connected GitHub file-management access used for this repository does not expose GitHub's sensitive Secrets API.


## Fast option: import your local .env file using GitHub CLI

The GitHub CLI can import a dotenv file directly into repository Actions secrets. From PowerShell, inside your project folder:

```powershell
gh auth status
gh secret set -f .env -R gajawadashashank-maker/srr-bazaar-automation
gh secret list -R gajawadashashank-maker/srr-bazaar-automation
```

This creates or updates repository Actions secrets for the non-commented entries in .env. It does not print their values. It requires GitHub CLI to be installed and authenticated to an account with permission to administer repository secrets.

Before running it, update your local .env with any newly rotated credentials. This imports extra environment entries too (such as business account IDs and the webhook verify token); unused entries do not hurt, but all imported values are stored as repository secrets.

The Actions workflow now maps WHATSAPP_ALLOWED_SENDERS from .env into the ALLOWED_SENDERS variable consumed by process_job.py. Cloudflare Worker configuration is separate: its own encrypted secrets and plain-text variables still need to be configured in Cloudflare Dashboard.

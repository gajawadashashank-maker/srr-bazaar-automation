/**
 * Secure Cloudflare bridge: Meta WhatsApp webhook -> GitHub Actions.
 * Required binding: Workers KV namespace named SEEN_MESSAGES.
 * Required encrypted secrets: GITHUB_PAT, WHATSAPP_VERIFY_TOKEN, META_APP_SECRET.
 */
const DEFAULT_OWNER = "gajawadashashank-maker";
const DEFAULT_REPO = "srr-bazaar-automation";

function jsonResponse(value, status) {
  return new Response(JSON.stringify(value), {
    status: status || 200,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}

function toHex(buffer) {
  return Array.from(new Uint8Array(buffer))
    .map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function constantTimeEqual(left, right) {
  if (left.length !== right.length) return false;
  let difference = 0;
  for (let i = 0; i < left.length; i++) {
    difference |= left.charCodeAt(i) ^ right.charCodeAt(i);
  }
  return difference === 0;
}

async function verifyMetaSignature(rawBody, signatureHeader, secret) {
  if (!secret || !signatureHeader || !signatureHeader.startsWith("sha256=")) return false;
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const digest = await crypto.subtle.sign("HMAC", key, rawBody);
  const expected = toHex(digest);
  const supplied = signatureHeader.slice(7).toLowerCase();
  return constantTimeEqual(expected, supplied);
}

function getAllowedSenders(env) {
  return new Set((env.ALLOWED_SENDERS || "")
    .split(",")
    .map((value) => value.trim().replace(/^\+/, ""))
    .filter(Boolean));
}

async function triggerGitHubAction(env, message, phoneNumberId) {
  const token = env.GITHUB_PAT;
  if (!token) throw new Error("GITHUB_PAT secret is missing");
  const owner = env.GITHUB_OWNER || DEFAULT_OWNER;
  const repo = env.GITHUB_REPO || DEFAULT_REPO;
  const url = "https://api.github.com/repos/" + owner + "/" + repo + "/dispatches";

  const response = await fetch(url, {
    method: "POST",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: "Bearer " + token,
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "SRR-Bazaar-Cloudflare-Worker",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      event_type: "whatsapp_submission",
      client_payload: {
        media_id: String(message.image.id),
        caption: String(message.image.caption || ""),
        sender: String(message.from || "").replace(/^\+/, ""),
        message_id: String(message.id || ""),
        phone_number_id: String(phoneNumberId || ""),
      },
    }),
  });

  if (response.status !== 204) {
    const detail = await response.text();
    throw new Error("GitHub dispatch failed with HTTP " + response.status + ": " + detail.slice(0, 250));
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "GET") {
      if (url.pathname === "/health") {
        return jsonResponse({ status: "ok", service: "srr-bazaar-webhook" }, 200);
      }
      const mode = url.searchParams.get("hub.mode");
      const token = url.searchParams.get("hub.verify_token");
      const challenge = url.searchParams.get("hub.challenge");
      if (mode === "subscribe" && token && token === env.WHATSAPP_VERIFY_TOKEN && challenge) {
        return new Response(challenge, {
          status: 200,
          headers: { "Content-Type": "text/plain; charset=utf-8" },
        });
      }
      return new Response("Forbidden", { status: 403 });
    }

    if (request.method !== "POST") return new Response("Method Not Allowed", { status: 405 });

    try {
      if (!env.META_APP_SECRET) {
        return jsonResponse({ error: "Meta signature secret is not configured" }, 503);
      }
      if (!env.SEEN_MESSAGES) {
        return jsonResponse({ error: "Workers KV binding SEEN_MESSAGES is not configured" }, 503);
      }
      const rawBody = await request.arrayBuffer();
      const signature = request.headers.get("x-hub-signature-256");
      const valid = await verifyMetaSignature(rawBody, signature, env.META_APP_SECRET);
      if (!valid) return new Response("Invalid Meta signature", { status: 401 });

      const payload = JSON.parse(new TextDecoder().decode(rawBody));
      const expectedPhoneId = String(env.WHATSAPP_PHONE_NUMBER_ID || "");
      const allowedSenders = getAllowedSenders(env);
      if (!expectedPhoneId || allowedSenders.size === 0) {
        return jsonResponse({ error: "Phone number ID or sender allowlist is not configured" }, 503);
      }

      let dispatched = 0;
      let skipped = 0;

      for (const entry of payload.entry || []) {
        for (const change of entry.changes || []) {
          const value = change.value || {};
          const metadata = value.metadata || {};
          const phoneNumberId = String(metadata.phone_number_id || "");
          if (phoneNumberId !== expectedPhoneId) {
            skipped += (value.messages || []).length;
            continue;
          }

          for (const message of value.messages || []) {
            if (message.type !== "image") {
              skipped++;
              continue;
            }

            const sender = String(message.from || "").replace(/^\+/, "");
            const image = message.image || {};
            const messageId = String(message.id || "");
            if (!messageId || !image.id || !allowedSenders.has(sender)) {
              skipped++;
              continue;
            }

            const key = "wa:" + messageId;
            if (await env.SEEN_MESSAGES.get(key)) {
              skipped++;
              continue;
            }

            // Store the dedupe marker only after GitHub accepts the dispatch.
            // A failed dispatch returns 502 so Meta can retry the webhook.
            await triggerGitHubAction(env, message, phoneNumberId);
            await env.SEEN_MESSAGES.put(key, "dispatched", { expirationTtl: 604800 });
            dispatched++;
          }
        }
      }

      return jsonResponse({ status: "accepted", dispatched: dispatched, skipped: skipped }, 200);
    } catch (error) {
      // Never log the raw webhook body, phone number, image caption, or credentials.
      console.error("WhatsApp webhook bridge failed:", error instanceof Error ? error.name : "UnknownError");
      return jsonResponse({ error: "Webhook dispatch failed; Meta can retry." }, 502);
    }
  },
};

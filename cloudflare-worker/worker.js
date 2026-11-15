/**
 * Cloudflare Worker for WhatsApp Cloud API -> GitHub Actions Bridge
 * Handles Meta Webhook verification (GET) and dispatches workflows on GitHub (POST).
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // 1. Meta Webhook Verification (GET)
    if (request.method === "GET") {
      const mode = url.searchParams.get("hub.mode");
      const token = url.searchParams.get("hub.verify_token");
      const challenge = url.searchParams.get("hub.challenge");

      if (mode === "subscribe" && token === env.WHATSAPP_VERIFY_TOKEN) {
        return new Response(challenge, {
          status: 200,
          headers: { "Content-Type": "text/plain" },
        });
      }
      return new Response("Forbidden", { status: 403 });
    }

    // 2. Meta Webhook Event (POST)
    if (request.method === "POST") {
      try {
        const rawBody = await request.text();

        // Optional Meta Signature verification if META_APP_SECRET is set
        if (env.META_APP_SECRET) {
          const sigHeader = request.headers.get("x-hub-signature-256") || "";
          const isValid = await verifyMetaSignature(rawBody, sigHeader, env.META_APP_SECRET);
          if (!isValid) {
            return new Response("Invalid signature", { status: 401 });
          }
        }

        const payload = JSON.parse(rawBody || "{}");
        const dispatched = [];

        // Parse WhatsApp payload
        for (const entry of payload.entry || []) {
          for (const change of entry.changes || []) {
            const value = change.value || {};
            const metadata = value.metadata || {};
            const phoneNumberId = metadata.phone_number_id;

            // Check phone number ID if configured
            if (env.WHATSAPP_PHONE_NUMBER_ID && phoneNumberId && phoneNumberId !== env.WHATSAPP_PHONE_NUMBER_ID) {
              continue;
            }

            for (const message of value.messages || []) {
              // Only process image messages
              if (message.type !== "image") {
                continue;
              }

              const sender = String(message.from || "").replace(/^\+/, "");
              const allowedSenders = (env.ALLOWED_SENDERS || "")
                .split(",")
                .map((s) => s.trim().replace(/^\+/, ""))
                .filter(Boolean);

              // Restrict to allowed senders if configured
              if (allowedSenders.length > 0 && !allowedSenders.includes(sender)) {
                console.log(`Ignoring image from unauthorized sender: ${sender}`);
                continue;
              }

              const imageData = message.image || {};
              const mediaId = imageData.id;
              const caption = imageData.caption || "";
              const messageId = message.id;

              if (mediaId) {
                // Trigger GitHub Actions repository_dispatch
                const ghResponse = await triggerGitHubAction(env, {
                  media_id: mediaId,
                  caption: caption,
                  sender: sender,
                  message_id: messageId,
                  phone_number_id: phoneNumberId,
                });

                dispatched.push({
                  message_id: messageId,
                  github_status: ghResponse.status,
                });
              }
            }
          }
        }

        // Meta requires an immediate 200 OK response
        return new Response(JSON.stringify({ status: "success", dispatched }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      } catch (err) {
        console.error("Error processing webhook:", err);
        // Return 200 to prevent Meta from spamming retries
        return new Response(JSON.stringify({ status: "error", error: err.message }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
    }

    return new Response("Method Not Allowed", { status: 405 });
  },
};

/**
 * Triggers GitHub Actions via repository_dispatch event
 */
async function triggerGitHubAction(env, clientPayload) {
  const repoOwner = env.GITHUB_OWNER || "gajawadashashank-maker";
  const repoName = env.GITHUB_REPO || "srr-bazaar-automation";
  const url = `https://api.github.com/repos/${repoOwner}/${repoName}/dispatches`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      Accept: "application/vnd.github.v3+json",
      Authorization: `Bearer ${env.GITHUB_PAT}`,
      "User-Agent": "SRR-Bazaar-Cloudflare-Worker",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      event_type: "whatsapp_submission",
      client_payload: clientPayload,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error(`GitHub dispatch failed (${response.status}): ${errorText}`);
  } else {
    console.log(`GitHub Action successfully dispatched for message: ${clientPayload.message_id}`);
  }

  return response;
}

/**
 * Verifies HMAC SHA-256 Meta webhook signature
 */
async function verifyMetaSignature(payload, signatureHeader, secret) {
  if (!signatureHeader || !signatureHeader.startsWith("sha256=")) {
    return false;
  }
  const expectedHash = signatureHeader.slice(7);
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const signature = await crypto.subtle.sign("HMAC", key, encoder.encode(payload));
  const hexHash = Array.from(new Uint8Array(signature))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");

  return hexHash === expectedHash;
}

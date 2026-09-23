import { createHmac, timingSafeEqual } from "node:crypto";

// បិទ BodyParser របស់ Vercel ដើម្បីចាប់យក Raw Body ដើម
export const config = {
  api: {
    bodyParser: false,
  },
};

// Function ទាញយក Raw Buffer ពី Request Stream
async function getRawBody(readable) {
  const chunks = [];
  for await (const chunk of readable) {
    chunks.push(typeof chunk === "string" ? Buffer.from(chunk) : chunk);
  }
  return Buffer.concat(chunks).toString("utf-8");
}

// Function Verify Signature តាម KHPayNow Docs
function verifySignature(headers, rawBody, secret) {
  const ts = headers["x-webhook-timestamp"];
  const sig = headers["x-webhook-signature"] || "";

  if (!ts || !sig || !secret) {
    return false;
  }

  const expected = "sha256=" + createHmac("sha256", secret).update(ts + "." + rawBody).digest("hex");
  const a = Buffer.from(sig);
  const b = Buffer.from(expected);

  return a.length === b.length && timingSafeEqual(a, b);
}

export default async function handler(req, res) {
  // អនុញ្ញាត GET សម្រាប់ Check Health / Ping
  if (req.method === "GET") {
    return res.status(200).json({ status: "Webhook endpoint is active" });
  }

  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method Not Allowed" });
  }

  try {
    const rawBody = await getRawBody(req);
    const secret = process.env.KHPAY_WEBHOOK_SECRET;

    // ផ្ទៀងផ្ទាត់ Signature ប្រសិនបើមាន Secret
    if (secret) {
      const isValid = verifySignature(req.headers, rawBody, secret);
      if (!isValid) {
        console.error("❌ Webhook Signature Mismatch");
        return res.status(401).json({ error: "Invalid signature" });
      }
    }

    let payload = {};
    if (rawBody) {
      try {
        payload = JSON.parse(rawBody);
      } catch (err) {
        console.warn("⚠️ JSON Parse Warning:", err.message);
      }
    }

    const { id, reference, provider, status, amount, currency } = payload;
    console.log(`✅ [Webhook Event] ID: ${id}, Ref: ${reference}, Provider: ${provider}, Status: ${status}, Amount: ${amount} ${currency}`);

    // ឆ្លើយតប status 200 ទៅ KHPayNow ភ្លាមៗ (< 10s)
    return res.status(200).json({ received: true });

  } catch (error) {
    console.error("❌ Webhook Error:", error);
    return res.status(500).json({ error: error.message });
  }
}

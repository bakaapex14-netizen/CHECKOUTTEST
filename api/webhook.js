import crypto from 'crypto';

export const config = {
  api: {
    bodyParser: false, // យក raw body សម្រាប់ verify signature
  },
};

async function getRawBody(readable) {
  const chunks = [];
  for await (const chunk of readable) {
    chunks.push(typeof chunk === 'string' ? Buffer.from(chunk) : chunk);
  }
  return Buffer.concat(chunks);
}

export default async function handler(req, res) {
  if (req.method === 'GET') {
    return res.status(200).json({ status: 'Webhook endpoint is active' });
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const secret = process.env.KHPAY_WEBHOOK_SECRET;
  const signature = req.headers['x-webhook-signature'] || '';
  const timestamp = req.headers['x-webhook-timestamp'] || '';

  const rawBodyBuffer = await getRawBody(req);
  const rawBody = rawBodyBuffer.toString('utf-8');

  if (secret) {
    const expected = "sha256=" + crypto.createHmac("sha256", secret).update(timestamp + "." + rawBody).digest("hex");
    if (signature !== expected) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
  }

  return res.status(200).json({ received: true });
}

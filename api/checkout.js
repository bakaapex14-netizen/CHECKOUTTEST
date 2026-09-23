export default async function handler(req, res) {
  // អនុញ្ញាតតែ POST
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method Not Allowed" });
  }

  const apiKey = process.env.KHPAY_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: "KHPAY_API_KEY is not set in Vercel Environment Variables" });
  }

  const { amount = "1.00", currency = "USD" } = req.body || {};
  const orderId = "order-" + Date.now();

  try {
    const response = await fetch("https://api.khpaynow.online/v1/payment", {
      method: "POST",
      headers: {
        "x-api-key": apiKey,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        amount: String(amount),
        currency: currency,
        provider: "aba", // អាចប្រើ "aba" ឬ "bakong"
        reference: orderId
      })
    });

    const data = await response.json();

    if (response.ok) {
      return res.status(200).json({
        success: true,
        payment_id: data.id,
        qr_link: data.qr_link,
        qr_string: data.qr_string
      });
    } else {
      return res.status(response.status).json({ success: false, error: data });
    }
  } catch (error) {
    return res.status(500).json({ success: false, error: error.message });
  }
}

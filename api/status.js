export default async function handler(req, res) {
  const { id } = req.query;
  const apiKey = process.env.KHPAY_API_KEY;

  if (!id) {
    return res.status(400).json({ error: 'Missing payment id' });
  }

  try {
    const response = await fetch(`https://api.khpaynow.online/v1/payment/status?id=${id}`, {
      headers: { "x-api-key": apiKey }
    });
    const data = await response.json();
    return res.status(response.status).json(data);
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
}

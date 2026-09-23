export default async function handler(req, res) {
  const { id } = req.query;
  const apiKey = process.env.KHPAY_API_KEY;

  if (!id || typeof id !== "string") {
    return res.status(400).json({ error: "Missing or invalid payment ID" });
  }

  if (!apiKey) {
    return res.status(500).json({ error: "KHPAY_API_KEY is not configured" });
  }

  try {
    const response = await fetch(`https://api.khpaynow.online/v1/payment/status?id=${encodeURIComponent(id)}`, {
      method: "GET",
      headers: { "x-api-key": apiKey }
    });

    const data = await response.json();
    const rawStatus = (data.status || "").toString().toLowerCase().trim();

    // ពិនិត្យស្ថានភាពជោគជ័យ
    const isPaid = 
      rawStatus === "paid" || 
      rawStatus === "approved" || 
      (rawStatus.length >= 20 && !["pending", "scanned", "failed", "expired"].includes(rawStatus));

    const isFailed = rawStatus === "failed" || rawStatus === "expired";
    const isScanned = rawStatus === "scanned";

    return res.status(response.status).json({
      id: id,
      status: rawStatus,
      paid: isPaid,
      failed: isFailed,
      scanned: isScanned
    });
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
}

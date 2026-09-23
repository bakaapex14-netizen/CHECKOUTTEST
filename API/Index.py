import os
import hmac
import hashlib
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load key ពី .env ប្រសិនបើ run នៅលើ Localhost
load_dotenv()

app = Flask(__name__)

# ទាញយក Key ពី Environment Variables
KHPAY_API_KEY = os.environ.get("KHPAY_API_KEY", "")
KHPAY_WEBHOOK_SECRET = os.environ.get("KHPAY_WEBHOOK_SECRET", "")
BASE_URL = "https://api.khpaynow.online"

# 1. API បង្កើត Payment
@app.route("/API/checkout", methods=["POST"])
def checkout():
    data = request.get_json(silent=True) or {}
    amount = data.get("amount", "1.00")
    currency = data.get("currency", "USD")
    order_id = data.get("reference", f"order-{int(request.date.timestamp() if request.date else 1000)}")

    headers = {
        "x-api-key": KHPAY_API_KEY,
        "content-type": "application/json"
    }
    payload = {
        "amount": str(amount),
        "currency": currency,
        "provider": "aba",
        "reference": order_id
    }

    try:
        response = requests.post(f"{BASE_URL}/v1/payment", json=payload, headers=headers)
        res_data = response.json()

        if response.status_code in [200, 201]:
            return jsonify({
                "success": True,
                "payment_id": res_data.get("id"),
                "qr_link": res_data.get("qr_link"),
                "qr_string": res_data.get("qr_string")
            })
        return jsonify({"success": False, "error": res_data}), response.status_code

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# 2. API ឆែកស្ថានភាព (Polling ពី KHPayNow API ដោយផ្ទាល់)
@app.route("/API/payment-status/<payment_id>", methods=["GET"])
def check_status(payment_id):
    headers = {"x-api-key": KHPAY_API_KEY}
    try:
        response = requests.get(f"{BASE_URL}/v1/payment/status?id={payment_id}", headers=headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 3. Webhook Endpoint (ទទួលទាំង /webhook និង /api/webhook)
@app.route("/webhook", methods=["GET", "POST"])
@app.route("/API/webhook", methods=["GET", "POST"])
def webhook():
    # ឆ្លើយតប 200 ភ្លាមបើប្រព័ន្ធធ្វើ Ping/Healthcheck តាមរយៈ GET
    if request.method == "GET":
        return jsonify({"status": "Webhook endpoint is active and listening"}), 200

    # ផ្នែក POST ពី KHPayNow
    timestamp = request.headers.get("x-webhook-timestamp", "")
    signature = request.headers.get("x-webhook-signature", "")
    raw_body = request.get_data()

    if not signature or not timestamp:
        return jsonify({"error": "Missing signature or timestamp headers"}), 400

    if not KHPAY_WEBHOOK_SECRET:
        print("[Warning] KHPAY_WEBHOOK_SECRET is not configured!")
        return jsonify({"error": "Server webhook secret not configured"}), 500

    # ផ្ទៀងផ្ទាត់ HMAC-SHA256 Signature
    message = timestamp.encode("utf-8") + b"." + raw_body
    expected_hash = hmac.new(
        KHPAY_WEBHOOK_SECRET.encode("utf-8"),
        message,
        hashlib.sha256
    ).hexdigest()
    expected_sig = f"sha256={expected_hash}"

    if not hmac.compare_digest(signature, expected_sig):
        print(f"[Webhook Error] Invalid signature. Received: {signature}, Expected: {expected_sig}")
        return jsonify({"error": "Invalid signature"}), 401

    payload = request.get_json(silent=True) or {}
    payment_id = payload.get("id")
    status = payload.get("status")

    print(f"[Webhook Success] Payment ID: {payment_id} is now {status}")

    # ត្រឡប់ 200 OK ភ្លាមៗទៅកាន់ KHPayNow
    return jsonify({"received": True}), 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)

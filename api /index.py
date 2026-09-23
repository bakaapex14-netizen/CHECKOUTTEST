import os
import hmac
import hashlib
import time
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ទាញយក API Key
KHPAY_API_KEY = os.environ.get("KHPAY_API_KEY", "")
KHPAY_WEBHOOK_SECRET = os.environ.get("KHPAY_WEBHOOK_SECRET", "")
BASE_URL = "https://api.khpaynow.online"

@app.route("/api/checkout", methods=["POST"])
def checkout():
    if not KHPAY_API_KEY:
        return jsonify({"success": False, "error": "KHPAY_API_KEY is not set in Vercel Environment Variables"}), 500

    data = request.get_json(silent=True) or {}
    amount = data.get("amount", "1.00")
    currency = data.get("currency", "USD")
    order_id = data.get("reference", f"order-{int(time.time())}")

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
        response = requests.post(f"{BASE_URL}/v1/payment", json=payload, headers=headers, timeout=10)
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


@app.route("/api/payment-status/<payment_id>", methods=["GET"])
def check_status(payment_id):
    headers = {"x-api-key": KHPAY_API_KEY}
    try:
        response = requests.get(f"{BASE_URL}/v1/payment/status?id={payment_id}", headers=headers, timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/webhook", methods=["GET", "POST"])
@app.route("/api/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return jsonify({"status": "Webhook is running"}), 200

    timestamp = request.headers.get("x-webhook-timestamp", "")
    signature = request.headers.get("x-webhook-signature", "")
    raw_body = request.get_data()

    if not signature or not timestamp:
        return jsonify({"error": "Missing headers"}), 400

    if not KHPAY_WEBHOOK_SECRET:
        return jsonify({"error": "KHPAY_WEBHOOK_SECRET not set"}), 500

    message = timestamp.encode("utf-8") + b"." + raw_body
    expected_hash = hmac.new(
        KHPAY_WEBHOOK_SECRET.encode("utf-8"),
        message,
        hashlib.sha256
    ).hexdigest()
    expected_sig = f"sha256={expected_hash}"

    if not hmac.compare_digest(signature, expected_sig):
        return jsonify({"error": "Invalid signature"}), 401

    return jsonify({"received": True}), 200

app = app 

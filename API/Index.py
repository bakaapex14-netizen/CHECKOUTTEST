import os
import hmac
import hashlib
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# ទាញយកតម្លៃពី file .env ពេល run នៅលើ localhost
load_dotenv()

app = Flask(__name__)

# អានតម្លៃពី environment variables
KHPAY_API_KEY = os.environ.get("KHPAY_API_KEY")
KHPAY_WEBHOOK_SECRET = os.environ.get("KHPAY_WEBHOOK_SECRET")
BASE_URL = "https://api.khpaynow.online"

# 1. API បង្កើត Payment
@app.route("/api/checkout", methods=["POST"])
def checkout():
    data = request.get_json() or {}
    amount = data.get("amount", "1.00")
    currency = data.get("currency", "USD")
    order_id = data.get("reference", f"order-{int(request.date.timestamp() if request.date else 12345)}")

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


# 2. API ឆែកស្ថានភាព (Polling ពី KHPayNow API ផ្ទាល់)
@app.route("/api/payment-status/<payment_id>", methods=["GET"])
def check_status(payment_id):
    headers = {"x-api-key": KHPAY_API_KEY}
    try:
        response = requests.get(f"{BASE_URL}/v1/payment/status?id={payment_id}", headers=headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 3. Webhook Endpoint
@app.route("/webhook", methods=["POST"])
def webhook():
    timestamp = request.headers.get("x-webhook-timestamp", "")
    signature = request.headers.get("x-webhook-signature", "")
    raw_body = request.get_data()

    # ផ្ទៀងផ្ទាត់ HMAC-SHA256 Signature
    message = timestamp.encode("utf-8") + b"." + raw_body
    expected_hash = hmac.new(
        KHPAY_WEBHOOK_SECRET.encode("utf-8"),
        message,
        hashlib.sha256
    ).hexdigest()
    expected_sig = f"sha256={expected_hash}"

    if not hmac.compare_digest(signature, expected_sig):
        return jsonify({"error": "Invalid signature"}), 401

    payload = request.get_json() or {}
    payment_id = payload.get("id")
    status = payload.get("status")

    # ចំណាំ៖ នៅលើ Serverless គ្មាន local memory ជាប់ទេ
    # ប្រសិនបើចង់រក្សាទុកក្នុង Database ពិតប្រាកដ (Supabase/PostgreSQL/MongoDB) ត្រូវ save នៅត្រង់នេះ
    print(f"[Webhook Event] Payment: {payment_id}, Status: {status}")

    return jsonify({"received": True}), 200

import razorpay
import os
from dotenv import load_dotenv

# load .env if needed
load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

print("🔑 Using keys:", RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET[:4] + "****")

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

try:
    order = client.order.create({
        "amount": 100,   # 1 INR (in paise)
        "currency": "INR",
        "payment_capture": "1"
    })
    print("✅ Razorpay order created successfully:")
    print(order)
except Exception as e:
    print("❌ Error creating order:", str(e))

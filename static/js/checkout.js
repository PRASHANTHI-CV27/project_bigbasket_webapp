document.addEventListener("DOMContentLoaded", async () => {
  const subtotalEl = document.getElementById("subtotal");
  const deliveryEl = document.getElementById("delivery");
  const savingsEl = document.getElementById("savings");
  const totalEl = document.getElementById("total");
  const payBtn = document.getElementById("proceed-pay-razor");

  const token = localStorage.getItem("token");
  if (!token) {
    alert("❌ Please log in first.");
    window.location.href = "/login/";
    return;
  }

  // --- Step 1: Load Cart Summary ---
  try {
    const res = await fetch("/api/cart/", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || "Failed to load cart");

    const subtotal = data.total || 0;
    const deliveryFee = 20; // example, static
    const savings = data.savings || 0;
    const finalTotal = subtotal + deliveryFee - savings;

    subtotalEl.textContent = subtotal;
    deliveryEl.textContent = deliveryFee;
    savingsEl.textContent = savings;
    totalEl.textContent = finalTotal;
  } catch (err) {
    console.error("Checkout load error:", err.message);
    return;
  }

  // --- Step 2: Handle Payment ---
  payBtn.addEventListener("click", async () => {
    payBtn.disabled = true;
    payBtn.textContent = "Processing...";

    try {
      // Create CartOrder
      let orderRes = await fetch("/api/checkout/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });
      let createdOrder = await orderRes.json();
      if (!orderRes.ok) throw new Error(createdOrder.detail);

      // Create Razorpay Order
      let razorpayRes = await fetch("/api/payments/create-razorpay-order/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ order_id: createdOrder.id, method: "razorpay" }),
      });
      let razorpayData = await razorpayRes.json();
      if (!razorpayRes.ok) throw new Error(razorpayData.detail);

      // Open Razorpay popup
      var options = {
        key: razorpayData.razorpay_key_id,
        amount: razorpayData.razorpay_amount,
        currency: razorpayData.razorpay_currency,
        order_id: razorpayData.razorpay_order_id,
        name: "BigBasket Clone",
        description: "Order Payment",
        handler: async function (response) {
          // Verify payment
          let verifyRes = await fetch("/api/payments/verify-razorpay-payment/", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              payment_id: razorpayData.payment_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_order_id: response.razorpay_order_id,
              razorpay_signature: response.razorpay_signature,
            }),
          });
          let verifyData = await verifyRes.json();
          if (verifyRes.ok) {
            alert("✅ Payment successful!");
            window.location.href = "/order-success-page/";
          } else {
            alert("❌ Payment verification failed: " + (verifyData.detail || "Unknown error"));
          }
        },
        modal: {
          ondismiss: function () {
            alert("Payment cancelled by user.");
            payBtn.disabled = false;
            payBtn.textContent = "Proceed to Pay with Razorpay";
          },
        },
      };
      var rzp1 = new Razorpay(options);
      rzp1.open();
    } catch (err) {
      alert("❌ Error: " + err.message);
      payBtn.disabled = false;
      payBtn.textContent = "Proceed to Pay with Razorpay";
    }
  });
});

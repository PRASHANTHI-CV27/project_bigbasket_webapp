document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ Razorpay checkout.js loaded");

  const payBtn = document.getElementById("proceed-pay-razor");

  if (payBtn) {
    payBtn.addEventListener("click", () => {
      console.log("👉 Pay button clicked");
      placeOrderRazorpay();
    });
  }

  // ====== LOAD CART ITEMS ======
async function loadCart() {
  const subtotalEl = document.getElementById("subtotal");
  const savingsEl = document.getElementById("savings");
  const totalEl = document.getElementById("total");
  const orderItemsEl = document.getElementById("order-items");

  const token = localStorage.getItem("token");
  if (!token) return;

  let res = await fetch("/api/cart/", {
    headers: { "Authorization": `Bearer ${token}` }
  });
  let data = await res.json();

  let subtotal = 0;
  orderItemsEl.innerHTML = "";

  if (data.items) {
    data.items.forEach(item => {
      const line = `<p>${item.product.title} × ${item.quantity} <span class="float-end">₹${item.line_total}</span></p>`;
      orderItemsEl.insertAdjacentHTML("beforeend", line);
    });
  }

  // ✅ Use backend total directly
  subtotal = parseFloat(data.total || 0);

  subtotalEl.textContent = `₹${subtotal.toFixed(2)}`;
  savingsEl.textContent = "-₹0.00";   // (you can add coupon logic later)
  totalEl.textContent = `₹${(subtotal + 20).toFixed(2)}`; // +delivery
}





  async function placeOrderRazorpay() {
    const token = localStorage.getItem("token");
    if (!token) {
      alert("❌ Please log in first");
      return;
    }

    // Step 1: Create order in your backend
    let orderRes = await fetch("/api/checkout/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ payment_method: "razorpay" })
    });

    let orderData = await orderRes.json();
    if (!orderRes.ok) {
      alert("❌ Checkout failed: " + (orderData.detail || "Unknown error"));
      return;
    }

    const orderId = orderData.id;

    // Step 2: Ask backend to create Razorpay order
    let res = await fetch("/api/payments/create-razorpay-order/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ order_id: orderId, method: "razorpay" })
    });

    let data = await res.json();
    if (!res.ok) {
      alert("❌ Failed to create Razorpay order");
      return;
    }

    console.log("✅ Razorpay order created:", data);

    // Step 3: Open Razorpay popup (official snippet)
    var options = {
      key: data.razorpay_key_id,          // from backend
      amount: data.razorpay_amount,       // amount in paise
      currency: data.razorpay_currency,
      order_id: data.razorpay_order_id,   // from backend
      name: "My Shop",
      description: "Order Payment",

      // ✅ Prefill avoids asking phone/email every time
      prefill: {
        name: "Test User",                // ideally from request.user
        email: "test@example.com",        // ideally from request.user.email
        contact: "9999999999"             // ideally from user profile
      },

      handler: async function (response) {
        console.log("👉 Razorpay response:", response);
        console.log("🔎 Verifying with:", {
        payment_id: data.payment_id,
        razorpay_payment_id: response.razorpay_payment_id,
        razorpay_order_id: response.razorpay_order_id,
        razorpay_signature: response.razorpay_signature
      });


        // Step 4: Verify payment with backend
        let verifyRes = await fetch("/api/payments/verify-razorpay-payment/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
          },
          body: JSON.stringify({
            payment_id: data.payment_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_order_id: response.razorpay_order_id,
            razorpay_signature: response.razorpay_signature
          })
        });

        let verifyData = await verifyRes.json();
        if (verifyRes.ok) {
          alert("✅ Payment successful!");
          window.location.href = "/orders/";
        } else {
          alert("❌ Payment failed: " + verifyData.detail);
        }
      },

      theme: { color: "#3399cc" }
    };

    var rzp = new Razorpay(options);
    rzp.open();
  }

  loadCart();
});

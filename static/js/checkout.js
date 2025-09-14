document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ checkout.js loaded");

  let subtotal = 0;
  const delivery = 20;
  let savings = 0;

  const subtotalEl = document.getElementById("subtotal");
  const savingsEl = document.getElementById("savings");
  const totalEl = document.getElementById("total");
  const orderItemsEl = document.getElementById("order-items");

  // ====== LOAD CART ITEMS ======
  async function loadCart() {
    const token = localStorage.getItem("token");
    if (!token) return;

    let res = await fetch("/api/cart/", {
      headers: { "Authorization": `Bearer ${token}` }
    });
    let data = await res.json();

    subtotal = 0;
    orderItemsEl.innerHTML = "";

    if (data.items) {
      data.items.forEach(item => {
        const line = `<p>${item.product.title} × ${item.quantity} <span class="float-end">₹${item.line_total}</span></p>`;
        orderItemsEl.insertAdjacentHTML("beforeend", line);
        subtotal += parseFloat(item.line_total);
      });
    }
    updateSummary();
  }

  // ====== UPDATE SUMMARY ======
  function updateSummary() {
    const couponApplied = document.getElementById("apply-coupon").checked;
    savings = couponApplied ? subtotal * 0.05 : 0;
    subtotalEl.textContent = `₹${subtotal.toFixed(2)}`;
    savingsEl.textContent = `-₹${savings.toFixed(2)}`;
    totalEl.textContent = `₹${(subtotal + delivery - savings).toFixed(2)}`;
  }

  document.getElementById("apply-coupon").addEventListener("change", updateSummary);

  // ====== ADDRESS ======
  document.getElementById("save-address").addEventListener("click", async () => {
    const address = document.getElementById("address-input").value;
    const pincode = document.getElementById("pincode-input").value;
    const country = document.getElementById("country-input").value;

    const token = localStorage.getItem("token");
    let res = await fetch("/api/addresses/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ address, pincode, country, status: true })
    });

    let data = await res.json();
    if (res.ok) {
      document.getElementById("default-address").textContent = data.address;
      alert("✅ Address updated");
    }
  });

  // ====== PAYMENT METHOD ======
  let selectedMethod = "cod";

  document.querySelectorAll(".methods-list li[data-method]").forEach(li => {
    li.addEventListener("click", () => {
      document.querySelectorAll(".methods-list li").forEach(i => i.classList.remove("active"));
      li.classList.add("active");
      selectedMethod = li.dataset.method;

      document.querySelectorAll(".method-content").forEach(div => div.style.display = "none");
      const activeDiv = document.getElementById(selectedMethod + "-form");
      if (activeDiv) activeDiv.style.display = "block";
    });
  });

  // ====== PAY (COD + Razorpay) ======
  document.getElementById("proceed-pay-cod").addEventListener("click", () => placeOrder("cod"));
  document.getElementById("proceed-pay-razor").addEventListener("click", () => placeOrder("razorpay"));

  async function placeOrder(method) {
    const token = localStorage.getItem("token");
    let res = await fetch("/api/checkout/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ payment_method: method })
    });

    let data = await res.json();
    if (res.ok) {
      alert(`✅ Order placed with ${method}! Invoice: ${data.invoice_no}`);
      window.location.href = "/";
    } else {
      alert("❌ Checkout failed: " + (data.detail || "Unknown error"));
    }
  }

  loadCart();
});

document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ checkout.js loaded");

  // =============== CHANGE ADDRESS ==================
  const changeBtn = document.getElementById("change-address");
  if (changeBtn) {
    changeBtn.addEventListener("click", () => {
      console.log("🟢 Change Address clicked");
      // Bootstrap modal opens automatically (data-bs-toggle="modal")
    });
  } else {
    console.warn("⚠️ Change Address button not found");
  }

  // Save new address inside modal
  const saveAddressBtn = document.getElementById("save-address");
  if (saveAddressBtn) {
    saveAddressBtn.addEventListener("click", async () => {
      console.log("🟢 Save Address clicked");
      const address = document.getElementById("address-input").value;
      const pincode = document.getElementById("pincode-input").value;
      const country = document.getElementById("country-input").value;

      if (!address || !pincode || !country) {
        alert("⚠️ Please fill all fields");
        return;
      }

      const token = localStorage.getItem("token");
      try {
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
          console.log("✅ Address saved:", data);
          document.getElementById("default-address").textContent = data.address;
          alert("✅ Address updated successfully!");
        } else {
          alert("❌ Failed to save address: " + (data.detail || "Unknown error"));
        }
      } catch (err) {
        console.error("❌ Error saving address", err);
      }
    });
  }

  // =============== PROCEED TO PAY ==================
  const payBtn = document.getElementById("proceed-pay");
  if (payBtn) {
    payBtn.addEventListener("click", async () => {
      console.log("🟢 Proceed to Pay clicked");

      const method = document.querySelector('input[name="payment"]:checked')?.value || "cod";
      console.log("Selected payment method:", method);

      await placeOrder(method);
    });
  } else {
    console.warn("⚠️ Proceed to Pay button not found");
  }
});

// =============== PLACE ORDER FUNCTION ==================
async function placeOrder(method) {
  const token = localStorage.getItem("token");
  if (!token) {
    alert("⚠️ You must log in to place an order.");
    return;
  }

  try {
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
      alert(`✅ Order placed successfully with ${method}! Invoice: ${data.invoice_no}`);
      window.location.href = "/"; // redirect to home (or order success page)
    } else {
      alert("❌ Checkout failed: " + (data.detail || "Unknown error"));
    }
  } catch (err) {
    console.error("❌ Error during checkout", err);
    alert("⚠️ Something went wrong during checkout.");
  }
}

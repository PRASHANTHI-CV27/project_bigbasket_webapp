document.addEventListener("DOMContentLoaded", async () => {
  console.log("✅ orders.js loaded");

  const ordersList = document.getElementById("orders-list");
  const token = localStorage.getItem("token");

  if (!token) {
    ordersList.innerHTML = `
      <div class="alert alert-warning">
        ⚠️ Please login to view your orders.
      </div>`;
    return;
  }

  try {
    // Show loading state while fetching
    ordersList.innerHTML = `<div class="text-center py-4">Loading your orders...</div>`;

    const res = await fetch("/api/orders/", {
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      }
    });

    const data = await res.json();
    console.log("Fetched orders:", data);

    if (!res.ok) {
      throw new Error(data.detail || "Failed to fetch orders");
    }

    if (data.length === 0) {
      ordersList.innerHTML = `
        <div class="text-center py-5">
          <img src="/static/images/no-orders.png" alt="No Orders" style="max-width:120px;" class="mb-3">
          <h5>No recent orders</h5>
          <p>You have not placed any order yet.</p>
          <a href="/" class="btn btn-success">Start Shopping</a>
        </div>`;
      return;
    }

    // Render orders
    ordersList.innerHTML = data.map(order => `
      <div class="card shadow-sm mb-3">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <h6 class="mb-1">Invoice: <span class="text-muted">${order.invoice_no}</span></h6>
              <small class="text-muted">Date: ${new Date(order.order_date).toLocaleString()}</small>
            </div>
            <span class="text-capitalize">
              ${order.order_status}
            </span>
          </div>
          <hr>
          <p class="mb-1">Total: <strong>₹${order.price}</strong></p>
          <p class="mb-0">Paid: ${order.paid_status ? "✅ Yes" : "❌ No"}</p>
        </div>
      </div>
    `).join("");

  } catch (err) {
    console.error("❌ Error fetching orders:", err);
    ordersList.innerHTML = `
      <div class="alert alert-danger">⚠️ Failed to load orders. Please try again later.</div>`;
  }
});

// Helper: Map status → badge color
function getStatusColor(status) {
  switch (status) {
    case "processing": return "warning";
    case "packed": return "info";
    case "shipped": return "primary";
    case "delivered": return "success";
    case "cancelled": return "danger";
    default: return "secondary";
  }
}

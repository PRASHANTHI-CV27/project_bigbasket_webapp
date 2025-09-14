document.addEventListener("DOMContentLoaded", () => {
  const body = document.getElementById("cart-items-body");
  const subtotalEl = document.getElementById("cart-subtotal");
  const savingsEl = document.getElementById("cart-savings");
  const token = localStorage.getItem("token");

  if (!token) {
    body.innerHTML = `<tr><td colspan="3" class="text-muted">Please login to view your cart.</td></tr>`;
    return;
  }

  // ----------------------
  // Load Cart
  // ----------------------
  async function loadCart() {
    try {
      let res = await fetch("/api/cart/", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        console.error("Cart fetch failed", res.status);
        body.innerHTML = `<tr><td colspan="3" class="text-danger">Failed to load cart.</td></tr>`;
        return;
      }

      let data = await res.json();
      console.log("Cart API response:", data);
      renderCart(data.items, data.total, data.savings || 0);
    } catch (err) {
      console.error("Cart load error:", err);
    }
  }

  // ----------------------
  // Render Cart
  // ----------------------
  function renderCart(items, total, savings) {
    if (!items.length) {
      body.innerHTML = `<tr><td colspan="3" class="text-muted">Your cart is empty.</td></tr>`;
      subtotalEl.textContent = "0";
      savingsEl.textContent = "0";
      return;
    }

    body.innerHTML = items.map(item => `
      <tr data-item-id="${item.id}">
        <td>
          <div class="d-flex align-items-center">
            <img src="${item.product.image || "/static/images/default.jpg"}" 
                 width="70" class="me-3 rounded border">
            <div>
              <div><strong>${item.product.title}</strong></div>
              <div class="text-muted small">
                ₹${item.price_snapshot}
                ${item.product.old_price ? `<del class="ms-1">₹${item.product.old_price}</del>` : ""}
              </div>
              <div class="text-muted small mt-1">
                <a href="#" class="text-danger remove-btn" data-id="${item.id}">Delete</a> |
                <a href="#" class="text-secondary save-btn" 
                   data-id="${item.id}" data-product-id="${item.product.id}"
                   data-title="${item.product.title}" 
                   data-image="${item.product.image || "/static/images/default.jpg"}" 
                   data-price="${item.product.price}">
                   Save for later
                </a>
              </div>
            </div>
          </div>
        </td>
        <td>
          <div class="input-group input-group-sm" style="width:140px">
            <button class="btn btn-outline-secondary minus-btn" data-id="${item.id}">-</button>
            <input type="text" class="form-control text-center qty-input" value="${item.quantity}" readonly>
            <button class="btn btn-outline-secondary plus-btn" data-id="${item.id}">+</button>
          </div>
        </td>
        <td class="item-subtotal">₹${item.line_total}</td>
      </tr>
    `).join("");

    subtotalEl.textContent = total;
    savingsEl.textContent = savings;

    attachEvents();
  }

  // ----------------------
  // Update Quantity
  // ----------------------
  async function updateQuantity(itemId, delta) {
    let res = await fetch(`/api/cart/${itemId}/`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ delta }),
    });
    loadCart();
  }

  // ----------------------
  // Remove Item
  // ----------------------
  async function removeItem(itemId) {
    await fetch(`/api/cart/${itemId}/`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    loadCart();
  }

  // ----------------------
  // Save for Later
  // ----------------------
  function saveForLater(productId, itemId, title, image, price) {
    let saved = JSON.parse(localStorage.getItem("savedItems") || "[]");

    if (!saved.find((s) => s.id == productId)) {
      saved.push({ id: productId, title, image, price });
    }

    localStorage.setItem("savedItems", JSON.stringify(saved));
    removeItem(itemId);
    renderSavedItems();
  }

  // ----------------------
  // Render Wishlist (Saved for Later)
  // ----------------------
  function renderSavedItems() {
    const container = document.getElementById("saved-items");
    if (!container) return;

    let savedItems = JSON.parse(localStorage.getItem("savedItems") || "[]");

    if (!savedItems.length) {
      container.innerHTML = `<p class="text-muted">No saved items</p>`;
      return;
    }

    container.innerHTML = savedItems.map(item => `
      <div class="col-md-3">
        <div class="card h-100 shadow-sm">
          <img src="${item.image}" class="card-img-top" 
               style="height:150px; object-fit:contain;" alt="${item.title}">
          <div class="card-body d-flex flex-column">
            <h6 class="card-title">${item.title}</h6>
            <p class="text-success">₹${item.price}</p>
            <button class="btn btn-sm btn-danger mt-auto move-to-cart-btn" data-id="${item.id}">
              Move to Cart
            </button>
          </div>
        </div>
      </div>
    `).join("");

    // Attach "Move to Cart" button listeners
    document.querySelectorAll(".move-to-cart-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const productId = btn.dataset.id;

        let res = await fetch("/api/cart/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token") || ""}`,
          },
          body: JSON.stringify({ product: productId, quantity: 1 }),
        });

        if (res.ok) {
          // remove from savedItems
          let savedItems = JSON.parse(localStorage.getItem("savedItems") || "[]");
          savedItems = savedItems.filter((p) => p.id != productId);
          localStorage.setItem("savedItems", JSON.stringify(savedItems));

          renderSavedItems();
          loadCart();
          if (typeof updateCartCount === "function") updateCartCount();
        }
      });
    });
  }

  // ----------------------
  // Attach Events
  // ----------------------
  function attachEvents() {
    document.querySelectorAll(".plus-btn").forEach((btn) =>
      btn.addEventListener("click", () => updateQuantity(btn.dataset.id, 1))
    );

    document.querySelectorAll(".minus-btn").forEach((btn) =>
      btn.addEventListener("click", () => updateQuantity(btn.dataset.id, -1))
    );

    document.querySelectorAll(".remove-btn").forEach((btn) =>
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        removeItem(btn.dataset.id);
      })
    );

    document.querySelectorAll(".save-btn").forEach((btn) =>
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        saveForLater(
          btn.dataset.productId,
          btn.dataset.id,
          btn.dataset.title,
          btn.dataset.image,
          btn.dataset.price
        );
      })
    );
  }

  // ----------------------
  // Initial Load
  // ----------------------
  loadCart();
  renderSavedItems();
});

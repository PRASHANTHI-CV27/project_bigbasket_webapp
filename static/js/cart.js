document.addEventListener("DOMContentLoaded", () => {
  const csrftoken = getCookie("csrftoken");

  // Increase/decrease quantity
  document.querySelectorAll(".plus-btn").forEach(btn => {
    btn.addEventListener("click", () => changeQuantity(btn.dataset.id, 1));
  });
  document.querySelectorAll(".minus-btn").forEach(btn => {
    btn.addEventListener("click", () => changeQuantity(btn.dataset.id, -1));
  });

  // Remove item
  document.querySelectorAll(".remove-btn").forEach(btn => {
    btn.addEventListener("click", e => {
      e.preventDefault();
      removeItem(btn.dataset.id);
    });
  });

  // Save for later (frontend only)
  document.querySelectorAll(".save-btn").forEach(btn => {
    btn.addEventListener("click", e => {
      e.preventDefault();
      saveForLater(btn.dataset.id);
    });
  });

  function changeQuantity(itemId, delta) {
    const row = document.querySelector(`tr[data-item-id='${itemId}']`);
    const qtyInput = row.querySelector(".qty-input");
    let current = parseInt(qtyInput.value, 10) || 0;
    const newQty = Math.max(1, current + delta);

    fetch(`/api/cart/${itemId}/`, {
      method: "PATCH",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken
      },
      body: JSON.stringify({ quantity: newQty })
    }).then(() => location.reload());
  }

  function removeItem(itemId) {
    fetch(`/api/cart/${itemId}/`, {
      method: "DELETE",
      credentials: "same-origin",
      headers: { "X-CSRFToken": csrftoken }
    }).then(() => location.reload());
  }

  function saveForLater(itemId) {
    const row = document.querySelector(`tr[data-item-id='${itemId}']`);
    const img = row.querySelector("img").src;
    const title = row.querySelector("strong").textContent;
    const price = row.querySelector(".item-subtotal").textContent;

    const saved = JSON.parse(localStorage.getItem("savedItems") || "[]");
    saved.push({ id: itemId, title, image: img, price });
    localStorage.setItem("savedItems", JSON.stringify(saved));

    removeItem(itemId);
  }

  // Render saved items
  const savedContainer = document.getElementById("saved-items");
  const saved = JSON.parse(localStorage.getItem("savedItems") || "[]");
  if (saved.length) {
    savedContainer.innerHTML = saved.map(p => `
      <div class="col-12 col-md-4">
        <div class="card p-2">
          <img src="${p.image}" class="card-img-top" style="height:100px;object-fit:contain">
          <div class="card-body p-2">
            <h6 class="card-title">${p.title}</h6>
            <p class="mb-1">${p.price}</p>
            <button class="btn btn-sm btn-primary move-to-cart" data-id="${p.id}">Move to cart</button>
          </div>
        </div>
      </div>
    `).join("");
  }

  function getCookie(name) {
    const v = document.cookie.split("; ").find(c => c.trim().startsWith(name + "="));
    return v ? decodeURIComponent(v.split("=")[1]) : null;
  }
});

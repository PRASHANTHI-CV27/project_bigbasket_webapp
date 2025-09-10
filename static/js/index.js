// ------------------- CONFIG -------------------
const PRODUCTS_URL = "/api/products/";
const ADD_TO_CART_URL = "/api/cart/add/";

// small helper to read Django CSRF cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
const csrftoken = getCookie("csrftoken");

// ------------------- ACTIONS -------------------

// Add product to cart
function addToCart(productId, qty = 1, btn) {
  fetch("/api/cart/", {
    method: "POST",   // 👈 must be POST
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrftoken,
    },
    body: JSON.stringify({
      product: productId,  // 👈 check if your API expects "product" or "product_id"
      quantity: qty
    }),
  })
    .then(async (res) => {
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Server error ${res.status}: ${errText}`);
      }
      return res.json();
    })
    .then(() => {

      refreshCartCount();

      if (btn) {
        btn.textContent = "Added";
        btn.classList.replace("btn-outline-danger", "btn-success");
        setTimeout(() => {
          btn.textContent = "Add";
          btn.classList.replace("btn-success", "btn-outline-danger");
        }, 1200);
      }
    })
    .catch((err) => {
      console.error("Add to cart error:", err);
      alert("Couldn't add to cart → " + err.message);
    });
}


// Save for later (UI only)
function saveForLaterUI(btn) {
  btn.classList.toggle("btn-outline-secondary");
  btn.classList.toggle("btn-warning");
}



// Refresh cart count badge
function refreshCartCount() {
  fetch("/api/cart/", { credentials: "same-origin" })
    .then(res => res.json())
    .then(data => {
      const count = data.items ? data.items.length : 0;
      const el = document.getElementById("cart-count");
      if (el) el.textContent = count;
    })
    .catch(err => console.error("Cart fetch failed", err));
}



// ------------------- UI RENDER -------------------

function createProductCard(product) {
  // Discount %
  let discount = null;
  if (
    product.old_price &&
    parseFloat(product.old_price) > parseFloat(product.price)
  ) {
    discount = Math.round(
      ((parseFloat(product.old_price) - parseFloat(product.price)) /
        parseFloat(product.old_price)) *
        100
    );
  }

  // Image
  let imageUrl = product.image || "/static/images/product-placeholder.png";

  // Pack options
  const packs =
    product.highlights && product.highlights.length
      ? product.highlights
      : ["500 g", "1 kg", "250 g"];

  // Card wrapper
  const wrapper = document.createElement("div");
  wrapper.className = "product-card";

  wrapper.innerHTML = `
    <div class="img-wrap">
      ${discount ? `<span class="discount-badge">${discount}% OFF</span>` : ""}
      <a href="/product/${product.id}/">
        <img src="${imageUrl}" alt="${product.title}">
      </a>
    </div>

    <div class="card-body">
      <div class="brand">${product.brand || "fresho!"}</div>
      <a href="/product/${product.id}/" class="title text-truncate">
        ${product.title}
      </a>

      <select class="form-select form-select-sm mt-2">
        ${packs.map((p) => `<option>${p}</option>`).join("")}
      </select>

      <div class="price-row mt-2">
        <div class="price-current">₹${product.price}</div>
        ${
          product.old_price
            ? `<div class="price-old">₹${product.old_price}</div>`
            : ""
        }
      </div>

      <button class="sasta-btn btn btn-sm btn-light w-100 mt-2">
        Har Din Sasta! <span style="float:right">▾</span>
      </button>

      <div class="bottom-row d-flex justify-content-between align-items-center mt-2">
        <button class="save-btn btn btn-outline-secondary btn-sm">
          <i class="bi bi-bookmark"></i>
        </button>
        <button class="add-btn btn btn-outline-danger btn-sm" data-product-id="${
          product.id
        }">
          Add
        </button>
      </div>
    </div>
  `;

  // Events
  wrapper.querySelector(".add-btn").addEventListener("click", function () {
    addToCart(product.id, 1, this);
  });

  wrapper.querySelector(".save-btn").addEventListener("click", function () {
    saveForLaterUI(this); // UI only
  });

  return wrapper;
}

// ------------------- INIT -------------------

document.addEventListener("DOMContentLoaded", function () {
  const productsRow = document.getElementById("products-row");
  const prevBtn = document.getElementById("prevBtn");
  const nextBtn = document.getElementById("nextBtn");

  let currentPage = 0;
  const itemsPerPage = 4;
  let cardWidth = 0;

  fetch(PRODUCTS_URL, { credentials: "same-origin" })
    .then((res) => res.json())
    .then((products) => {
      products.forEach((p) => {
        const card = createProductCard(p);
        productsRow.appendChild(card);
      });

     // compute card width dynamically (with margin)
      const firstCard = productsRow.querySelector(".product-card");
      const style = window.getComputedStyle(firstCard);
      const marginRight = parseInt(style.marginRight);
      const cardWidth = firstCard.offsetWidth + marginRight;

        // fix viewport width = exactly 4 cards
      const viewport = document.querySelector(".products-viewport");
      viewport.style.width = cardWidth * itemsPerPage + "px";

        // max pages
      const maxPage = Math.ceil(products.length / itemsPerPage) - 1;


      // Next
      nextBtn.addEventListener("click", () => {
        if (currentPage < maxPage) {
          currentPage++;
          productsRow.style.transform = `translateX(-${
            cardWidth * itemsPerPage * currentPage
          }px)`;
          prevBtn.disabled = false;
          if (currentPage === maxPage) nextBtn.disabled = true;
        }
      });

      // Prev
      prevBtn.addEventListener("click", () => {
        if (currentPage > 0) {
          currentPage--;
          productsRow.style.transform = `translateX(-${
            cardWidth * itemsPerPage * currentPage
          }px)`;
          nextBtn.disabled = false;
          if (currentPage === 0) prevBtn.disabled = true;
        }
      });
    });
});

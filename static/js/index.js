// home.js - load products, render cards, add-to-cart + wishlist actions
document.addEventListener("DOMContentLoaded", function () {

  // Config - change URLs if your APIs differ
  const PRODUCTS_URL = "/api/products/";
  const ADD_TO_CART_URL = "/api/cart/add/";
  const CART_URL = "/api/cart/";
  const WISHLIST_URL = "/api/wishlist/";   // POST add {product: id}, DELETE remove /api/wishlist/<id>/

  // small helper to read Django CSRF cookie
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + "=")) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  const csrftoken = getCookie("csrftoken");

  // update cart badge from GET /api/cart/
  function refreshCartCount() {
    fetch(CART_URL, { credentials: 'same-origin' })
      .then(r => r.ok ? r.json() : Promise.reject(r))
      .then(data => {
        const count = data.items ? data.items.length : 0;
        const el = document.getElementById("cart-count");
        if (el) el.textContent = count;
      }).catch(()=>{ /* ignore unauthenticated */ });
  }

  // Add product to cart (productId, qty)
  function addToCart(productId, qty=1, btn) {
    // require login - if server returns 401/403 we'll redirect
    fetch(ADD_TO_CART_URL, {
      method: "POST",
      credentials: 'same-origin',
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken
      },
      body: JSON.stringify({ product: productId, quantity: qty })
    })
    .then(res => {
      if (res.status === 401 || res.status === 403) {
        // not logged in -> redirect to login
        window.location.href = "/login/?next=" + encodeURIComponent(window.location.pathname);
        return;
      }
      if (!res.ok) return res.json().then(j => Promise.reject(j));
      return res.json();
    })
    .then(data => {
      refreshCartCount();
      if (btn) {
        btn.classList.remove("btn-outline-danger");
        btn.classList.add("btn-danger");
        btn.textContent = "Added";
        setTimeout(()=>{ btn.classList.remove("btn-danger"); btn.classList.add("btn-outline-danger"); btn.textContent = "Add"; }, 1100);
      }
    })
    .catch(err=>{
      console.error("Add to cart error", err);
      alert("Couldn't add to cart. Try login or check server.");
    });
  }

  // Wishlist toggle (simple: POST to add, DELETE to remove)
  function toggleWishlist(productId, iconEl) {
    // decide from icon state
    const active = iconEl.dataset.wish === "1";
    if (!active) {
      // add
      fetch(WISHLIST_URL, {
        method: "POST",
        credentials: 'same-origin',
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken
        },
        body: JSON.stringify({ product: productId })
      }).then(r => {
        if (r.status === 401 || r.status === 403) {
          window.location.href = "/login/?next=" + encodeURIComponent(window.location.pathname);
          return;
        }
        if (!r.ok) return r.json().then(j => Promise.reject(j));
        return r.json();
      }).then(data=>{
        iconEl.dataset.wish = "1";
        iconEl.classList.add("text-danger");
      }).catch(err=>{
        console.error("wishlist add", err);
      });
    } else {
      // remove - we assume endpoint DELETE /api/wishlist/<id>/ or send product id to delete endpoint (change if different)
      // try both: if the icon has data-wish-id use it, else use productId in a delete path
      const wishId = iconEl.dataset.wishId;
      const delUrl = wishId ? `${WISHLIST_URL}${wishId}/` : `${WISHLIST_URL}${productId}/`;
      fetch(delUrl, {
        method: "DELETE",
        credentials: 'same-origin',
        headers: { "X-CSRFToken": csrftoken }
      }).then(r => {
        if (r.status === 401 || r.status === 403) {
          window.location.href = "/login/?next=" + encodeURIComponent(window.location.pathname);
          return;
        }
        if (!r.ok) return r.json().then(j => Promise.reject(j));
        iconEl.dataset.wish = "0";
        iconEl.classList.remove("text-danger");
      }).catch(err=>{
        console.error("wishlist remove", err);
      });
    }
  }

  // create a single product card DOM element
  function createProductCard(product) {
    // compute discount
    let discount = null;
    if (product.old_price && parseFloat(product.old_price) > 0 && parseFloat(product.old_price) > parseFloat(product.price)) {
      discount = Math.round(((parseFloat(product.old_price) - parseFloat(product.price)) / parseFloat(product.old_price)) * 100);
    }

    // image: prefer first of product.images array if present
    let imageUrl = "";
    if (product.images && product.images.length) {
      // product.images items may have .images (see serializer) or be direct URL
      const first = product.images[0];
      imageUrl = first && first.images ? first.images : (first.url || "");
    }
    if (!imageUrl) imageUrl = product.image || "/static/images/product-placeholder.png";

    // pack options come from product.highlights or fallback
    const packs = (product.highlights && product.highlights.length) ? product.highlights : ["250 g", "500 g", "1 pc"];

    // create element
    const wrapper = document.createElement("div");
    wrapper.className = "product-card";

    wrapper.innerHTML = `
      <div class="img-wrap">
        <button class="wish-btn" title="Save for later" data-product-id="${product.id}" data-wish="0">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#666" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 1 0-7.8 7.8l1 1L12 21l8.8-8.6 1-1a5.5 5.5 0 0 0 0-7.8z"/></svg>
        </button>

        ${ discount ? `<span class="discount-badge">${discount}% OFF</span>` : "" }
        <img src="${imageUrl}" alt="${product.title}">
      </div>

      <div class="card-body">
        <div class="brand">fresho!</div>
        <div class="title">${product.title}</div>

        <div class="pack-dropdown">
          <div class="dropdown">
            <button class="btn btn-sm btn-outline-secondary dropdown-toggle w-100" type="button" data-bs-toggle="dropdown">
              ${packs[0]}
            </button>
            <ul class="dropdown-menu">
              ${packs.map(p => `
                <li>
                  <a class="dropdown-item pack-option" href="#" data-pack="${p}">
                    <div class="d-flex justify-content-between align-items-center">
                      <div>
                        <small class="text-success">${discount ? discount + "% OFF" : ""}</small>
                        <div class="fw-bold">₹${product.price}</div>
                      </div>
                      <div class="delivery-chip">⚡ 9 MINS</div>
                    </div>
                  </a>
                </li>`).join("")}
            </ul>
          </div>
        </div>

        <div class="price-row">
          <div class="price-current">₹${product.price}</div>
          ${product.old_price ? `<div class="price-old">₹${product.old_price}</div>` : ""}
        </div>

        <button class="sasta-btn">Har Din Sasta! <span style="float:right">▾</span></button>

        <div class="bottom-row">
          <div class="bookmark-btn" title="Bookmark / Save"></div>
          <button class="add-btn" data-product-id="${product.id}">Add</button>
        </div>
      </div>
    `;

    // events: add to cart
    const addBtn = wrapper.querySelector(".add-btn");
    addBtn.addEventListener("click", function() {
      const productId = this.dataset.productId;
      addToCart(productId, 1, this);
    });

    // wishlist button
    const wishBtn = wrapper.querySelector(".wish-btn");
    wishBtn.addEventListener("click", function(e) {
      e.preventDefault();
      const pid = this.dataset.productId;
      toggleWishlist(pid, this);
    });

    // pack option clicks update the text on button and (if you want) recalc price
    wrapper.querySelectorAll(".pack-option").forEach(a => {
      a.addEventListener("click", function(e){
        e.preventDefault();
        const pack = this.dataset.pack;
        const btn = wrapper.querySelector(".pack-dropdown .dropdown-toggle");
        btn.textContent = pack;
        // optionally recalc price here if you have per-pack prices
      });
    });

    return wrapper;
  }

  // fetch & render
  const productsRow = document.getElementById("products-row");
  fetch(PRODUCTS_URL, { credentials: 'same-origin' })
    .then(res => res.json())
    .then(list => {
      // if your API wraps results e.g. { results: [...] } handle that
      const products = Array.isArray(list) ? list : (list.results || []);
      products.forEach(p => {
        const card = createProductCard(p);
        const col = document.createElement("div");
        col.className = "col-auto";
        col.appendChild(card);
        productsRow.appendChild(col);
      });
    })
    .catch(err => {
      console.error("Error loading products:", err);
      productsRow.innerHTML = "<div class='text-muted p-3'>Failed to load products.</div>";
    });

  // scroll controls
  document.getElementById("nextBtn").addEventListener("click", () => {
    productsRow.scrollBy({ left: 280, behavior: "smooth" });
  });
  document.getElementById("prevBtn").addEventListener("click", () => {
    productsRow.scrollBy({ left: -280, behavior: "smooth" });
  });

  // init cart count
  refreshCartCount();
});

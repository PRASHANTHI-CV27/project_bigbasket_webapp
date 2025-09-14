console.log("✅ index.js loaded!");
fetch("/api/products/").then(r => r.json()).then(d => console.log(d));


document.addEventListener("DOMContentLoaded", async () => {
  const PRODUCTS_URL = "/api/products/";
  const CATEGORIES_URL = "/api/categories/";
  const productsRow = document.getElementById("products-row");
  const viewport = document.querySelector(".products-viewport");
  const prevBtn = document.getElementById("prevBtn");
  const nextBtn = document.getElementById("nextBtn");

  // --- 1. Fetch categories ---
  const categoryRes = await fetch(CATEGORIES_URL);
  const categories = await categoryRes.json();
  const categoryMap = {};
  categories.forEach(c => {
    categoryMap[c.id] = (c.name ? c.name.toLowerCase() : "others");
  });

  // --- 2. Fetch products ---
  const productRes = await fetch(PRODUCTS_URL);
  let products = await productRes.json();

  console.log("Products received:", products.length);

  productsRow.innerHTML = "";

  // --- 3. Loop products and build cards ---
  products.forEach(product => {
    const cname = categoryMap[product.category] || "others";

    // category → unit options
    const categoryRules = {
      vegetables: ["250 g", "500 g", "1 kg"],
      fruits: ["250 g", "500 g", "1 kg"],
      cereals: ["500 g", "1 kg", "5 kg"],
      bakery: ["1 packet"],
      dairy: ["1 packet"],
      snacks: ["1 packet"],
      others: ["1 pc"]
    };

    const units = categoryRules[cname] || categoryRules["others"];

    const basePrice = parseFloat(product.price);
    const baseOld = parseFloat(product.old_price);

    // first option prices
    const mult = weightToMultiplier(units[0]);
    const firstPrice = (basePrice * mult).toFixed(2);
    const firstOld = baseOld ? (baseOld * mult).toFixed(2) : null;

    const discount = firstOld && firstOld > firstPrice
      ? Math.round(((firstOld - firstPrice) / firstOld) * 100)
      : 0;

    // --- 3a. Create card container ---
    const card = document.createElement("div");
    card.className = "product-card";

    // --- 3b. Card HTML ---
    card.innerHTML = `
      <div class="img-wrap clickable">
        ${discount ? `<div class="discount-badge">${discount}% OFF</div>` : ""}
        <img src="${getImageUrl(product)}" alt="${product.title}">
        <div class="delivery-badge">5 MINS</div>
      </div>

      <p class="text-muted small mb-1">${product.brand || "fresho!"}</p>
      <h6 class="clickable">${product.title}</h6>

      ${units.length > 1
        ? `<select class="form-select form-select-sm variant-select mb-2">
            ${units.map(u => {
              const m = weightToMultiplier(u);
              const price = (basePrice * m).toFixed(2);
              const old = baseOld ? (baseOld * m).toFixed(2) : "";
              return `<option data-price="${price}" data-old="${old}">${u}</option>`;
            }).join("")}
          </select>`
        : `<div class="small text-muted mb-2">${units[0]}</div>`
      }

      <div class="price-row">
        <span class="price-current">₹${firstPrice}</span>
        ${firstOld ? `<span class="price-old">₹${firstOld}</span>` : ""}
      </div>

      <div class="offer-strip">Har Din Sasta!</div>

      <div class="bottom-row ">
      <button class="wishlist-btn" data-id="${product.id}">
        <i class="bi bi-bookmark"></i>
      </button>
      <button class="add-to-cart-btn" data-id="${product.id}">
        Add
      </button>
      </div>

    `;

    // --- 3c. Append to row ---
    productsRow.appendChild(card);

    // --- 3d. Dropdown change event ---
    const select = card.querySelector(".variant-select");
    if (select) {
      const priceRow = card.querySelector(".price-row");
      select.addEventListener("change", e => {
        const opt = e.target.selectedOptions[0];
        const newPrice = parseFloat(opt.dataset.price).toFixed(2);
        const newOld = opt.dataset.old ? parseFloat(opt.dataset.old).toFixed(2) : null;

        priceRow.innerHTML = `
          <span class="price-current">₹${newPrice}</span>
          ${newOld ? `<span class="price-old">₹${newOld}</span>` : ""}
        `;
      });
    }

    const addBtn = card.querySelector(".add-to-cart-btn");
addBtn.addEventListener("click", async () => {
  const csrftoken = getCookie("csrftoken");
  const productId = addBtn.dataset.id;

  let res = await fetch("/api/cart/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrftoken,
      "Authorization": `Bearer ${localStorage.getItem("token") || ""}`
    },
    body: JSON.stringify({ product: productId, quantity: 1 })
  });

  if (res.ok) {
    addBtn.textContent = "Added ✓";
    addBtn.disabled = true;

    if (typeof updateCartCount === "function") {
      updateCartCount();
    }
  } else {
    console.error("Add failed", await res.json());
  }
});

// --- 3f. Wishlist button ---
  const wishBtn = card.querySelector(".wishlist-btn");
  if (wishBtn){
  wishBtn.addEventListener("click", () => {
  let savedItems = JSON.parse(localStorage.getItem("savedItems") || "[]");
  const productData = {
    id: product.id,
    title: product.title,
    image: getImageUrl(product),
    price: product.price
  };

  if (!savedItems.find(p => p.id === product.id)) {
    savedItems.push(productData);
    localStorage.setItem("savedItems", JSON.stringify(savedItems));
    wishBtn.innerHTML = "<i class='bi bi-bookmark-fill'></i>";
  } else {
      savedItems = savedItems.filter(p => p.id !== product.id);
      localStorage.setItem("savedItems", JSON.stringify(savedItems));
      wishBtn.innerHTML = `<i class="bi bi-bookmark"></i>`; // Reset
  }
});
  }  

    // --- 3e. Make image & title clickable ---
    const img = card.querySelector("img");
    const title = card.querySelector("h6");

    [img, title].forEach(el => {
      if (el) {
        el.style.cursor = "pointer";
        el.addEventListener("click", () => {
          console.log("➡ Redirecting to:", `/product/${product.id}/`);
          window.location.href = `/product/${product.id}/`;
        });
      }
    });
  });

  // --- Helpers ---
  function getImageUrl(product) {
    if (product.image) return product.image;
    return "https://via.placeholder.com/220x220?text=No+Image";
  }

  function weightToMultiplier(label) {
    if (!label) return 1;
    label = label.toLowerCase();
    if (label.includes("kg")) return parseFloat(label) || 1;
    if (label.includes("g")) return (parseFloat(label) || 0) / 1000;
    return 1; // for "pc", "packet"
  }

  // --- 4. Arrows for carousel ---
  function stepAmount() {
    const card = productsRow.querySelector(".product-card");
    if (!card) return viewport.clientWidth;
    const style = getComputedStyle(card);
    const gap = parseFloat(style.marginRight) || 16;
    const per = Math.max(1, Math.floor(viewport.clientWidth / (card.offsetWidth + gap)));
    return (card.offsetWidth + gap) * per;
  }

  prevBtn.addEventListener("click", () => {
    viewport.scrollBy({ left: -stepAmount(), behavior: "smooth" });
  });
  nextBtn.addEventListener("click", () => {
    viewport.scrollBy({ left: stepAmount(), behavior: "smooth" });
  });
});


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

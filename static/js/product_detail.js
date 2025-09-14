console.log("✅ index.js loaded!");

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

    // --- Create card ---
    const card = document.createElement("div");
    card.className = "product-card";

    card.innerHTML = `
      <div class="img-wrap">
        <img src="${getImageUrl(product)}" alt="${product.title}">
      </div>

      <p class="text-muted small mb-1">${product.brand || "fresho!"}</p>
      <h6>${product.title}</h6>

      <div class="price-row">
        <span class="price-current">₹${product.price}</span>
        ${product.old_price ? `<span class="price-old">₹${product.old_price}</span>` : ""}
      </div>

      <div class="offer-strip">Har Din Sasta!</div>

      <div class="bottom-row">
        <button class="btn btn-sm btn-light">♡</button>
        <button class="add-btn add-to-cart-btn" data-id="${product.id}">Add</button>
      </div>
    `;

    productsRow.appendChild(card);

    // --- Redirect to product detail when clicking image or title ---
    const img = card.querySelector("img");
    const title = card.querySelector("h6");

    [img, title].forEach(el => {
      el.style.cursor = "pointer";
      el.addEventListener("click", () => {
        window.location.href = `/product/${product.id}/`;
      });
    });
  });

  // --- Helpers ---
  function getImageUrl(product) {
    if (product.image) return product.image;
    return "https://via.placeholder.com/220x220?text=No+Image";
  }

  // --- 4. Carousel arrows ---
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

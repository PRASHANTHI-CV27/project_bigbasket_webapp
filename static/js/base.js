document.addEventListener('DOMContentLoaded', () => {
  
  const categoryList = document.getElementById('category-list');

  // Fetch categories
  fetch('/api/categories/')
    .then(res => res.json())
    .then(data => {
      const categories = data.results ? data.results : data;
      categoryList.innerHTML = categories.map(cat => `
        <li><a class="dropdown-item" href="/category/${cat.id}/">${cat.title}</a></li>
      `).join('');
    })
    .catch(err => {
      console.error("Failed to load categories", err);
      categoryList.innerHTML = '<li><span class="dropdown-item text-muted">No categories</span></li>';
    });

  // Call cart count update once on load
  updateCartCount();
});

// Function to open auth modal
function openAuthModel() {
  const modal = new bootstrap.Modal(document.getElementById('authModal'));
  modal.show();
}

// 🔥 Global function so other scripts (index.js, cart.js) can use it
function updateCartCount() {
  const token = localStorage.getItem("token");
  const cartCountEl = document.getElementById("cart-count");

  if (!cartCountEl) return;

  // If no token → reset to empty
  if (!token) {
    cartCountEl.textContent = "";
    return;
  }

  fetch("/api/cart/", {
    headers: { "Authorization": `Bearer ${token}` }
  })
    .then(res => res.json())
    .then(data => {
      if (data.items) {
        // ✅ Show total quantity, not just number of products
        const totalQty = data.items.reduce((sum, item) => sum + item.quantity, 0);
        cartCountEl.textContent = totalQty > 0 ? totalQty : "";
      }
    })
    .catch(err => {
      console.error("Cart count update failed:", err);
      cartCountEl.textContent = "";
    });
}



// function updateLoginUI() {
//   const token = localStorage.getItem("token");
//   const userMenu = document.getElementById("user-menu");

//   if (!userMenu) return;

//   if (token) {
//     // Logged in → profile dropdown
//     userMenu.innerHTML = `
//       <div class="dropdown">
//         <a href="#" class="btn btn-dark dropdown-toggle d-flex align-items-center" 
//            id="userDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
//           <i class="bi bi-person-circle fs-5"></i>
//         </a>
//         <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="userDropdown">
//           <li><a class="dropdown-item" href="/profile/">Profile</a></li>
//           <li><a class="dropdown-item" href="/wishlist/">Wishlist</a></li>
//           <li><a class="dropdown-item" href="/orders/">My Orders</a></li>
//           <li><hr class="dropdown-divider"></li>
//           <li><a class="dropdown-item text-danger" href="#" id="logout-btn">Logout</a></li>
//         </ul>
//       </div>
//     `;

//     // Logout handler
//     document.getElementById("logout-btn").addEventListener("click", () => {
//       localStorage.removeItem("token");
//       localStorage.removeItem("refresh");
//       showTemporaryMessage("Logged out successfully", 3000);
//       updateLoginUI();
//       window.location.href = "/";
//     });

//   } else {
//     // Logged out → black login button
//     userMenu.innerHTML = `
//       <button class="btn btn-dark login-btn" 
//               type="button" data-bs-toggle="modal" data-bs-target="#authModal">
//         Login / Signup
//       </button>
//     `;
//   }
// }

// // Run when page loads
// document.addEventListener("DOMContentLoaded", updateLoginUI);

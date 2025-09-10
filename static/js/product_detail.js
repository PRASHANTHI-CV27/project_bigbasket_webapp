document.addEventListener("DOMContentLoaded", () => {
  const mainImage = document.getElementById("main-image");
  const zoomedImage = document.getElementById("zoomed-image");
  const zoomResult = document.getElementById("zoom-result");

  // Hover zoom
  mainImage.addEventListener("mouseenter", () => {
    zoomResult.classList.remove("d-none");
  });
  mainImage.addEventListener("mouseleave", () => {
    zoomResult.classList.add("d-none");
  });
  mainImage.addEventListener("mousemove", (e) => {
    const rect = mainImage.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const xPercent = (x / rect.width) * 100;
    const yPercent = (y / rect.height) * 100;

    const zoomWidth = zoomedImage.offsetWidth - zoomResult.offsetWidth;
    const zoomHeight = zoomedImage.offsetHeight - zoomResult.offsetHeight;

    zoomedImage.style.left = -(xPercent * 12) + "px";
    zoomedImage.style.top = -(yPercent * 12) + "px";
  });

  // Thumbnail click → change main image
  document.querySelectorAll(".thumb").forEach(thumb => {
    thumb.addEventListener("click", () => {
      mainImage.src = thumb.src;
      zoomedImage.src = thumb.src;
    });
  });

  // Add to cart
  const csrftoken = getCookie("csrftoken");
  const addBtn = document.getElementById("add-to-cart-btn");
  if (addBtn) {
    addBtn.addEventListener("click", () => {
      const productId = addBtn.dataset.id;
      fetch("/api/cart/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({ product: productId, quantity: 1 }),
      })
        .then(res => res.json())
        .then(() => {
          addBtn.textContent = "Added";
          addBtn.classList.replace("btn-danger", "btn-success");

            if (typeof updateCartCount === "function") {
              updateCartCount();
            }

          setTimeout(() => {
            addBtn.textContent = "Add to basket";
            addBtn.classList.replace("btn-success", "btn-danger");
          }, 1200);
        })
        .catch(err => console.error("Add to cart error:", err));
    });
  }

  function getCookie(name) {
    const v = document.cookie.split("; ").find(c => c.startsWith(name + "="));
    return v ? decodeURIComponent(v.split("=")[1]) : null;
  }
});

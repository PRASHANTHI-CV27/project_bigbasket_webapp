// document.addEventListener("DOMContentLoaded", () => {
//   console.log("✅ vendor.js loaded");

//   // Sidebar navigation
//   document.querySelectorAll("a[data-section]").forEach(link => {
//     link.addEventListener("click", e => {
//       e.preventDefault();
//       const target = link.getAttribute("data-section");

//       // Hide all sections
//       document.querySelectorAll(".content-section").forEach(sec => sec.classList.add("d-none"));

//       // Show target section
//       document.getElementById(target + "-section").classList.remove("d-none");

//       // Active link style
//       document.querySelectorAll("nav .nav-link").forEach(nav => nav.classList.remove("active"));
//       link.classList.add("active");
//     });
//   });

//   // Later: Fetch vendor profile/products/orders here
// });

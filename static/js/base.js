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
});

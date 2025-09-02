# BigBasket Clone - E-commerce Project

This is a Django + DRF based e-commerce web application inspired by **BigBasket**.  
It supports multiple user roles:
- **Admin** → manages everything
- **Vendor (Seller)** → can add products
- **Buyer (Customer)** → can browse, add to cart, order, and pay

## Tech Stack
- **Backend**: Django, Django REST Framework (DRF)
- **Database**: SQLite (default) → PostgreSQL (production-ready)
- **Authentication**: JWT (SimpleJWT)
- **Frontend**: Django Templates (basic), extendable to React

## Features
- User roles: Admin, Vendor, Buyer
- Vendor adds products under categories
- Buyer adds to cart, wishlist, places orders
- Order & Payment tracking
- Admin panel with full control (like BigBasket reference)
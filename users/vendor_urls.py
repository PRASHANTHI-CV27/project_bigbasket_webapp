from django.urls import path
from . import views

urlpatterns = [
    path("", views.vendor_dashboard, name="vendor-dashboard"),
    path("profile/", views.vendor_profile, name="vendor-profile"),
    path("products/", views.vendor_products, name="vendor-products"),
    path("orders/", views.vendor_orders, name="vendor-orders"),
    
    path("edit-profile/", views.vendor_edit_profile, name="vendor-edit-profile"),
    path("products/add/", views.add_product, name="add-product"),
    path("products/<int:pk>/edit/", views.edit_product, name="edit-product"),
    path("products/<int:pk>/delete/", views.delete_product, name="delete-product"),
    path("vendor/orders/", views.vendor_orders, name="vendor-orders"),
    path("vendor/orders/<int:pk>/status/", views.update_order_status, name="update-order-status"),
]





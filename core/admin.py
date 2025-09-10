from django.contrib import admin
from core.models import Product, Category, Vendor, CartOrder,CartOrderItems, ProductImages, ProductReview, WishList, Address,Tags,Cart, CartItem


class ProductImagesAdmin(admin.TabularInline):
    model = ProductImages

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImagesAdmin]
    list_display = ['user','title', 'product_image','price','product_status','category']
    search_fields = ['title']
    
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'category_image']
    
class VendorAdmin(admin.ModelAdmin):
    list_display = ['title', 'vendor_image']
    
class CartOrderAdmin(admin.ModelAdmin):
    list_display = ['user','price','paid_status','order_date','order_status','invoice_no',]
    
class CartOrderItemsAdmin(admin.ModelAdmin):
    list_display = ['order', 'item', 'item_status','image', 'qty','price','total']
    
    
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['user','product', 'review','rating','date']
    
    
class WishListAdmin(admin.ModelAdmin):
    list_display = ['user','product', 'date']


class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'address', 'status']
    
class TagsAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    
    
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('price_snapshot',)

class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_id', 'created_at']
    inlines = [CartItemInline]

class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'product', 'quantity', 'price_snapshot']
    search_fields = ['product__title']
    

    


admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Vendor, VendorAdmin)
admin.site.register(CartOrder, CartOrderAdmin)
admin.site.register(CartOrderItems, CartOrderItemsAdmin)
admin.site.register(ProductReview, ProductReviewAdmin)
admin.site.register(WishList, WishListAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Tags, TagsAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
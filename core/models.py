from django.db import models
from shortuuid.django_fields import ShortUUIDField
from django.conf import settings
from django.utils.html import mark_safe
from unicodedata import decimal
from users.models import User
from decimal import Decimal

PRODUCT_STATUS = (
    ('active', 'Active'),
    ('out of stock', 'Out of Stock'),
    ('inactive', 'Inactive'),
    ('coming_soon', 'Coming_soon'),
    ('discontinued', 'Discontinued'),
    
)

CART_STATUS = (
    ('in_cart', 'In Cart'),
    ('saved_for_later', 'Saved for later'),
    ('removed', 'Removed'),
)

ORDER_STATUS = (
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('packed', 'Packed'),
    ('shipped', 'Shipped'),
    ('out_for_delivery', 'Out for Delivery'),
    ('delivered', 'Delivered'),
    ('cancelled', 'Cancelled'),
    ('returned', 'Returned'),
)

PAYMENT_STATUS = (
    ('pending', 'Pending'),
    ('successful', 'Successful'),
    ('failed', 'Failed'),
    ('refunded', 'Refunded'),
)

RATING = (
    ('1', '⭐'),
    ('2', '⭐⭐'),
    ('3', '⭐⭐⭐'),
    ('4', '⭐⭐⭐⭐'),
    ('5', '⭐⭐⭐⭐⭐'),
)

def user_directory_path(instance, filename):
    return 'user_{0}/{1}'.format(instance.user.id, filename)

# Create your models here.
class Category(models.Model):
    cid = ShortUUIDField(unique=True, length=10, max_length=20, prefix="cat", alphabet="abcdefgh12345", editable=True, default="")
    title = models.CharField(max_length=100, default="category title")   #title or heading
    image = models.ImageField(upload_to='category', default="default.jpg")
    parent = models.ForeignKey(                 # self-referencing for subcategories
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children"
    ) 
    
    
    class Meta:
        verbose_name_plural = "Categories"
        db_table = "core_category"
        
    def category_image(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % (self.image.url))

    def __str__(self):
        return self.title
    
    
class Tags(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    
class Vendor(models.Model):
    vid = ShortUUIDField(unique=True, length=10, max_length=20, prefix="ven", alphabet="abcdefghijk12345", editable=True, default="")
    title = models.CharField(max_length=100, default="vendor title")   
    image = models.ImageField(upload_to='user_directory_path', default="default.jpg")
    description = models.TextField(null=True, blank=True, default="vendor description")
    address = models.CharField(max_length=100, default="Bangalore")
    contact = models.CharField(max_length=100, default="+91 123(456)789")
    
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null = True)
    
    class Meta:
        verbose_name_plural = "Vendors"
        
    def vendor_image(self):
            return mark_safe('<img src="%s" width="50" height="50" />' % (self.image.url))
        
    def __str__(self):
        return self.title
    
class Product(models.Model):

    pid = ShortUUIDField(unique=True, length=10, max_length=20, prefix= "pro",alphabet="abcdefghi12345678", editable=True, default="")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey("core.Category", on_delete=models.SET_NULL, null=True)
    vendor = models.ForeignKey("core.Vendor", on_delete=models.SET_NULL, null=True)

    brand = models.CharField(max_length=100, default="fresho!", blank=True, null=True)
    title = models.CharField(max_length=100, default="product title")
    image = models.ImageField(upload_to='user_directory_path', default="default.jpg")
    description = models.TextField(null=True, blank=True, default=" product description")
    
    price = models.DecimalField(max_digits=10, decimal_places=2, default=66.00) 
    old_price = models.DecimalField(max_digits=10, decimal_places=2, default=None, null=True, blank=True)

    specifications = models.TextField(null=True, blank=True, )
    tags = models.ManyToManyField(Tags, blank=True, related_name="products")
    product_status = models.CharField(choices=PRODUCT_STATUS, max_length=20, default="in_review")

    # in_stock = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    highlights = models.JSONField(default=list, blank=True)
    
    sku = ShortUUIDField(unique=True, length=4, max_length=10, prefix= "sku", alphabet="1234567890", editable=False)
    

    date = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Products"
        db_table = "core_product"
        
    def product_image(self):
            return mark_safe('<img src="%s" width="50" height="50" />' % (self.image.url))
        
    def __str__(self):
        return self.title
    
    
    
    def get_dpercentage(self):
        new_price = (self.price / self.old_price) * 100
        return new_price
    
class ProductImages(models.Model):
    images = models.ImageField(upload_to='product-images', default= "product.jpg")
    product = models.ForeignKey("core.Product", on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name_plural = "Product Images"
        db_table = "core_productimage"
        
####################################cart, order,Items and address#############################################        
        



class CartOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    invoice_no = models.CharField(max_length=200, unique=True, null=True, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    paid_status = models.BooleanField(default=False)
    order_date = models.DateTimeField(auto_now_add=True)
    order_status = models.CharField(choices=ORDER_STATUS, max_length=30, default="processing")
    
    
    class Meta:
        verbose_name_plural = "Cart Order"
        db_table = "core_cartorder"
        
    def save(self, *args, **kwargs):
        # Auto-generate invoice if missing
        if not self.invoice_no:
            self.invoice_no = uuid.uuid4().hex[:12].upper()

        # Auto-update order price from items if already created
        if self.pk:
            total = sum([item.total for item in self.cartorderitems_set.all()])
            self.price = total

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.invoice_no} ({self.user})"

class CartOrderItems(models.Model):
    order = models.ForeignKey("core.CartOrder", on_delete=models.CASCADE)
    product = models.ForeignKey("core.Product", on_delete=models.SET_NULL, null=True, blank=True)
    item_status = models.CharField(choices = ORDER_STATUS, max_length=200, default="processing")  # was product_status
    item = models.CharField(max_length=200)  # product title
    image = models.ImageField(upload_to='user_directory_path', max_length=200, blank=True, null=True)
    qty = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # unit price
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)  # qty * price

    class Meta:
        verbose_name_plural = "Cart Order Items"

    def save(self, *args, **kwargs):
        # Auto-calc total
        self.total = Decimal(self.qty) * self.price
        super().save(*args, **kwargs)

    def image_tag(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="50" height="50" />')
        return "No Image"
    image_tag.short_description = "Product Image"

    def __str__(self):
        return f"{self.qty} × {self.item} (Order {self.order.invoice_no})"
    
    
    
    
    
    
    #######################################product review, wish list, address###################################


class ProductReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey("core.Product", on_delete=models.SET_NULL, null=True)
    review = models.TextField()
    rating = models.CharField(choices=RATING, max_length=1, default=None)
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Product Reviews"
        db_table = "core_productreview"
        
    def __str__(self):
        return self.product.title
    
    def get_rating(self):
        return self.rating
    
    
class WishList(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey("core.Product", on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Wishlists"
        
    def __str__(self):
        return self.product.title
    
    
class Address(models.Model): 
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    address = models.CharField(max_length=200, default="address")
    status = models.BooleanField(default=False)
    
    
    ############################cart##########################
    
    
    

class Cart(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"
        db_table = "core_cart"

    def __str__(self):
        if self.user:
            return f"Cart {self.id} (user={self.user})"
        return f"Cart {self.id} (session={self.session_id})"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)

    class Meta:
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        db_table = "core_cartitem"
        unique_together = ('cart', 'product')
        
    def save(self, *args, **kwargs):
        # Auto-fill snapshot price from product if empty or 0
        if self.product and ( self.price_snapshot is None or self.price_snapshot == 0):
            self.price_snapshot = self.product.price
        super().save(*args, **kwargs)
        
    
    @property
    def line_total(self):
        """Quantity × Price Snapshot"""
        if self.price_snapshot:
            return self.quantity * self.price_snapshot
        return Decimal('0.00')

    def __str__(self):
        return f"{self.quantity} x {self.product} (cart {self.cart_id})"

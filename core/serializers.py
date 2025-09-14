from rest_framework import serializers
from .models import Product,Category ,ProductImages, CartOrder, CartOrderItems, Cart, CartItem, CartOrder, CartOrderItems, Vendor, Address

# Serializer for extra product images
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImages
        fields = ['id', 'images']


# Serializer for main Product model
class ProductSerializer(serializers.ModelSerializer):
    # include multiple images
    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    # method to fetch all related images
    def get_images(self, obj):
        qs = ProductImages.objects.filter(product=obj)
        return ProductImageSerializer(qs, many=True, context=self.context).data






class CategorySerializer(serializers.ModelSerializer):
    # return absolute image URL when request is present
    image = serializers.SerializerMethodField()
    # parent will be returned as the parent's PK (or null)
    parent = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'cid', 'title', 'image', 'parent']

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url
    
    
    
 # if ProductSerializer already exists

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    line_total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
         # use model property
        read_only=True
    )

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'price_snapshot', 'line_total']



class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    savings = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'session_id', 'items', 'total','savings']

    def get_total(self, obj):
        return sum([item.quantity * item.price_snapshot for item in obj.items.all()])
    
    def get_savings(self, obj):
        savings = 0
        for item in obj.items.all():
            if item.product.old_price:
                savings += (float(item.product.old_price) - float(item.price_snapshot)) * item.quantity
        return savings





class CartOrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    """
    Serializer for each item inside an order.
    Uses the model fields you already have.
    """
    class Meta:
        model = CartOrderItems
        fields = [
            'id',
            'product',
            'item_status',
            'item',
            'image',
            'qty',
            'price',
            'total',
        ]
        read_only_fields = ( 'total')


class CartOrderSerializer(serializers.ModelSerializer):
    """
    Serializer for an order. Includes nested items (read-only).
    `source='cartorderitems_set'` uses Django's default related name
    since your CartOrderItems FK did not set a related_name.
    """
    items = CartOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = CartOrder
        fields = [
            'id',
            'user',
            'invoice_no',
            'price',
            'paid_status',
            'order_date',
            'order_status',
            'items',
        ]
        read_only_fields = ('price', 'paid_status', 'order_date', 'invoice_no')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            if not (request.user.is_staff or request.user.is_superuser):
                # For non-admins (customers/vendors), hide user field
                data.pop('user', None)
        return data
        
        


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"
         # vendor.user will be set automatically


class CartOrderItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartOrderItems
        fields = ['id', 'item_status']






class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        # expose id, address text and status (status = default)
        fields = ["id", "address", "status"]
        read_only_fields = ["id"]

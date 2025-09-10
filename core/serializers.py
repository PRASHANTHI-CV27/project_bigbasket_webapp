from rest_framework import serializers
from .models import Product,Category ,ProductImages, CartOrder, CartOrderItems, Cart, CartItem, CartOrder, CartOrderItems

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
        source='line_total',  # use model property
        read_only=True
    )

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'price_snapshot', 'line_total']



class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'session_id', 'items', 'total']

    def get_total(self, obj):
        return sum([item.quantity * item.price_snapshot for item in obj.items.all()])





class CartOrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for each item inside an order.
    Uses the model fields you already have.
    """
    class Meta:
        model = CartOrderItems
        fields = [
            'id',
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
    items = CartOrderItemSerializer(source='cartorderitems_set', many=True, read_only=True)

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

from rest_framework import serializers
from .models import Crop, MarketListing, Order, Product

class CropSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crop
        fields = '__all__'

class MarketListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketListing
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

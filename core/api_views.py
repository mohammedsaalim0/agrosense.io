from rest_framework import viewsets, permissions
from .models import Crop, MarketListing, Order, Product
from .serializers import CropSerializer, MarketListingSerializer, OrderSerializer, ProductSerializer

class CropViewSet(viewsets.ModelViewSet):
    queryset = Crop.objects.all()
    serializer_class = CropSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class MarketListingViewSet(viewsets.ModelViewSet):
    queryset = MarketListing.objects.all()
    serializer_class = MarketListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

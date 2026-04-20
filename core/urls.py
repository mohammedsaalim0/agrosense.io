from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/recommend/', views.api_recommend, name='api_recommend'),
    path('api/market/', views.api_market_data, name='api_market_data'),
    path('api/scan/', views.api_scan, name='api_scan'),
    path('api/create-listing/', views.api_create_listing, name='api_create_listing'),
    path('api/remove-listing/', views.api_remove_listing, name='api_remove_listing'),
    path('api/apply-scheme/', views.api_apply_scheme, name='api_apply_scheme'),
    path('api/cancel-application/', views.api_cancel_application, name='api_cancel_application'),
    path('register/', views.register, name='register'),
]

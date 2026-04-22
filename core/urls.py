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
    path('api/edu/progress/', views.api_update_learning_progress, name='api_update_learning_progress'),
    path('api/edu/assessment/', views.api_submit_assessment, name='api_submit_assessment'),
    path('api/edu/certificate/', views.api_generate_certificate, name='api_generate_certificate'),
    path('register/', views.register, name='register'),
    path('store/', views.agro_store, name='agro_store'),
    path('agro-suggestion/', views.agro_suggestion, name='agro_suggestion'),
    path('api/place-order/', views.api_place_order, name='api_place_order'),
    path('api/weather-soil/', views.api_weather_soil, name='api_weather_soil'),
    path('api/my-orders/', views.api_my_orders, name='api_my_orders'),
    path('api/cancel-order/', views.api_cancel_order, name='api_cancel_order'),
    path('api/generate-bill/', views.api_generate_bill, name='api_generate_bill'),
    path('api/search-market/', views.api_search_market, name='api_search_market'),
    path('api/schemes/', views.api_get_schemes, name='api_get_schemes'),
    path('api/predict-fair-price/', views.api_predict_fair_price, name='api_predict_fair_price'),
]

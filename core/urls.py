from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from . import views, api_views

router = DefaultRouter()
router.register(r'crops', api_views.CropViewSet)
router.register(r'market-listings', api_views.MarketListingViewSet)
router.register(r'orders', api_views.OrderViewSet, basename='order')
router.register(r'products', api_views.ProductViewSet)

urlpatterns = [
    # PWA Routes
    path('manifest.json', TemplateView.as_view(template_name='core/manifest.json', content_type='application/json')),
    path('service-worker.js', TemplateView.as_view(template_name='core/service-worker.js', content_type='application/javascript')),
    path('sw.js', TemplateView.as_view(template_name='core/service-worker.js', content_type='application/javascript')),
    
    # Main Routes
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
    path('order/bill/<str:order_id>/', views.download_invoice, name='download_invoice'),
    path('order/bill/<str:order_id>/', views.download_invoice, name='download_invoice'),
    path('api/search-market/', views.api_search_market, name='api_search_market'),
    path('api/schemes/', views.api_get_schemes, name='api_get_schemes'),
    path('api/predict-fair-price/', views.api_predict_fair_price, name='api_predict_fair_price'),
    path('api/check-auth/', views.api_check_auth, name='api_check_auth'),
    path('api/create-razorpay-order/', views.api_create_razorpay_order, name='api_create_razorpay_order'),
    path('api/verify-razorpay-payment/', views.api_verify_razorpay_payment, name='api_verify_razorpay_payment'),
    path('terms/', views.terms_and_conditions, name='terms'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('shipping/', views.shipping_policy, name='shipping'),
    path('contact/', views.contact_us, name='contact'),
    path('refunds/', views.refund_policy, name='refunds'),
    path('admin/analytics/', views.admin_analytics, name='admin_analytics'),
    path('api/submit-grievance/', views.api_submit_grievance, name='api_submit_grievance'),
    path('api/submit-refund/', views.api_submit_refund, name='api_submit_refund'),
    path('offline/', views.offline, name='offline'),
    
    # Smart Irrigation Routes
    path('smart-irrigation/', views.smart_irrigation, name='smart_irrigation'),
    path('api/irrigation/status/', views.irrigation_status_api, name='irrigation_status_api'),
    path('api/irrigation/water-now/', views.irrigation_water_now_api, name='irrigation_water_now_api'),
    path('api/irrigation/stop-watering/', views.irrigation_stop_watering_api, name='irrigation_stop_watering_api'),
    path('api/irrigation/settings/', views.irrigation_settings_api, name='irrigation_settings_api'),
    path('api/irrigation/moisture-history/', views.irrigation_moisture_history_api, name='irrigation_moisture_history_api'),
    
    # Smart IoT Chamber URLs
    path('smart-chamber/', views.smart_chamber_dashboard, name='smart_chamber_dashboard'),
    path('api/chamber/dashboard/', views.chamber_dashboard_api, name='chamber_dashboard_api'),
    path('api/chamber/crop-environments/', views.crop_environments_api, name='crop_environments_api'),
    path('api/chamber/select-crop/', views.select_crop_environment_api, name='select_crop_environment_api'),
    path('api/chamber/manual-control/', views.manual_control_api, name='manual_control_api'),
    path('api/chamber/sensor-history/', views.sensor_history_api, name='sensor_history_api'),
    path('api/chamber/irrigation-schedule/', views.irrigation_schedule_api, name='irrigation_schedule_api'),
    path('api/chamber/alerts/', views.system_alerts_api, name='system_alerts_api'),
    path('api/chamber/control-logs/', views.chamber_control_logs_api, name='chamber_control_logs_api'),
]

from django.contrib import admin
from django.utils.html import format_html
from .models import Profile, Crop, SupportScheme, MarketListing, SchemeApplication, LearningProgress, CourseCertificate, CourseAssessment, Product, Order, BankTransaction, RefundRequest

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'mrp', 'quantity_weight', 'rating', 'is_organic', 'in_stock', 'image_preview')
    list_filter = ('category', 'is_organic', 'in_stock')
    search_fields = ('name', 'category')
    list_editable = ('price', 'mrp', 'in_stock')
    readonly_fields = ('image_preview',)
    fieldsets = (
        ('Product Info', {
            'fields': ('name', 'category', 'description', 'quantity_weight', 'rating', 'is_organic', 'in_stock')
        }),
        ('Pricing', {
            'fields': ('price', 'mrp')
        }),
        ('Product Image', {
            'fields': ('image_upload', 'image_url', 'image_preview'),
            'description': 'Upload an image directly OR paste a public image URL. Uploaded image takes priority.'
        }),
    )

    def image_preview(self, obj):
        url = obj.get_image()
        if url:
            return format_html('<img src="{}" style="height:80px; border-radius:8px; object-fit:cover;" />', url)
        return "No Image"
    image_preview.short_description = "Preview"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'full_name', 'phone', 'total_amount', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('order_id', 'full_name', 'phone')
    readonly_fields = ('created_at',)
    list_editable = ('status',)

@admin.register(SupportScheme)
class SupportSchemeAdmin(admin.ModelAdmin):
    list_display = ('title', 'provider', 'amount', 'category')
    list_filter = ('category',)
    search_fields = ('title', 'provider')

@admin.register(MarketListing)
class MarketListingAdmin(admin.ModelAdmin):
    list_display = ('crop_name', 'quantity', 'price', 'seller_name', 'location', 'quality', 'is_verified')
    list_filter = ('is_verified', 'quality')
    search_fields = ('crop_name', 'seller_name', 'location')
    list_editable = ('is_verified',)

@admin.register(SchemeApplication)
class SchemeApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'scheme_name', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('user__username', 'scheme_name')
    list_editable = ('status',)

admin.site.register(Profile)
admin.site.register(Crop)
admin.site.register(LearningProgress)
admin.site.register(CourseCertificate)
admin.site.register(CourseAssessment)
admin.site.register(BankTransaction)

@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    list_display = ('refund_id', 'user', 'order', 'refund_amount', 'payment_preference', 'status', 'submitted_at')
    list_filter = ('status', 'payment_preference', 'submitted_at')
    search_fields = ('refund_id', 'user__username', 'order__order_id', 'upi_id')
    readonly_fields = ('refund_id', 'submitted_at', 'updated_at', 'user', 'order', 'reason_category', 'reason_details', 'refund_amount', 'payment_preference', 'upi_id', 'bank_account_no', 'bank_ifsc', 'bank_account_name', 'evidence_image')
    list_editable = ('status',)
    fieldsets = (
        ('Refund Info', {'fields': ('refund_id', 'user', 'order', 'refund_amount', 'status', 'submitted_at', 'updated_at')}),
        ('Reason', {'fields': ('reason_category', 'reason_details', 'evidence_image')}),
        ('Payment Details', {'fields': ('payment_preference', 'upi_id', 'bank_account_no', 'bank_ifsc', 'bank_account_name')}),
    )

# Customize admin site header
admin.site.site_header = "AgroSense Admin Portal"
admin.site.site_title = "AgroSense Admin"
admin.site.index_title = "Welcome to the AgroSense Store Management Panel"

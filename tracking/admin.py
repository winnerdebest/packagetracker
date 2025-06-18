from django.contrib import admin
from .models import Package, DeliveryHistory

class DeliveryHistoryInline(admin.TabularInline):
    model = DeliveryHistory
    extra = 1

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['tracking_number', 'status', 'current_city', 'estimated_delivery', 'updated_at']
    list_filter = ['status']
    search_fields = ['tracking_number', 'current_city']
    inlines = [DeliveryHistoryInline]

@admin.register(DeliveryHistory)
class DeliveryHistoryAdmin(admin.ModelAdmin):
    list_display = ['package', 'city', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['package__tracking_number', 'city']

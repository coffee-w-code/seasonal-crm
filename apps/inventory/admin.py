from django.contrib import admin
from apps.customers.models import Customer
from .models import Product, InventoryItem, StockMovement, StockAudit

admin.site.register(Product)
admin.site.register(InventoryItem)
admin.site.register(Customer)
admin.site.register(StockMovement)
admin.site.register(StockAudit)

from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("transaction_type", "transaction_reference", "customer_msisdn", "amount", "status", "created_at")
    search_fields = ("transaction_reference", "customer_msisdn", "transaction_id")
    list_filter = ("transaction_type", "status", "created_at")

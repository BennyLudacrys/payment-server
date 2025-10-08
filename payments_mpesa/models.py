from django.db import models

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('C2B', 'Customer to Business'),
        ('B2C', 'Business to Customer'),
    )
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPES)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    conversation_id = models.CharField(max_length=100, null=True, blank=True)
    transaction_reference = models.CharField(max_length=20)
    third_party_reference = models.CharField(max_length=20)
    customer_msisdn = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20)  # success ou error
    message = models.TextField(null=True, blank=True)
    raw_response = models.JSONField(null=True, blank=True)  # guarda resposta completa da API
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.transaction_reference} - {self.status}"

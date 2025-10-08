from django.db import models

class Transaction(models.Model):
    trans_id = models.CharField(max_length=30, unique=True)
    msisdn = models.CharField(max_length=20, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    content = models.TextField(blank=True)
    ref_no = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=50, default='pending')
    request_id = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.trans_id
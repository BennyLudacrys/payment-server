"""
Modelos de banco de dados para transações M-Pesa e tokens OAuth.
"""

from django.db import models
from django.utils import timezone


class OAuthToken(models.Model):
    """Modelo para armazenar tokens OAuth2 gerados."""
    client_id = models.CharField(max_length=255)
    access_token = models.CharField(max_length=255, unique=True, db_index=True)
    token_type = models.CharField(max_length=50, default='Bearer')
    expires_in = models.IntegerField(help_text="Tempo de expiração em segundos")
    expires_at = models.DateTimeField(help_text="Data e hora de expiração")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Token OAuth"
        verbose_name_plural = "Tokens OAuth"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Token para {self.client_id} - Expira em {self.expires_at}"
    
    def is_valid(self):
        """Verifica se o token ainda é válido."""
        return timezone.now() < self.expires_at


class Transaction(models.Model):
    """Modelo para armazenar transações M-Pesa e eMola."""
    
    TRANSACTION_TYPES = [
        ('C2B', 'Customer to Business'),
        ('B2C', 'Business to Customer'),
    ]
    
    STATUS_CHOICES = [
        ('success', 'Sucesso'),
        ('error', 'Erro'),
        ('pending', 'Pendente'),
    ]
    
    # Campos principais
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    transaction_id = models.CharField(max_length=100, null=True, blank=True, 
                                     help_text="ID da transação retornado pelo M-Pesa")
    conversation_id = models.CharField(max_length=100, null=True, blank=True,
                                      help_text="ID da conversa retornado pelo M-Pesa")
    transaction_reference = models.CharField(max_length=20, db_index=True,
                                            help_text="Referência interna da transação")
    third_party_reference = models.CharField(max_length=20, db_index=True,
                                            help_text="Referência de terceiros (UUID)")
    
    # Dados do cliente
    customer_msisdn = models.CharField(max_length=15, db_index=True,
                                      help_text="Número de telefone do cliente (formato: 258XXXXXXXXX)")
    
    # Valor da transação
    amount = models.DecimalField(max_digits=12, decimal_places=2,
                                help_text="Valor da transação em Meticais")
    
    # Status e mensagens
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    message = models.TextField(null=True, blank=True,
                              help_text="Mensagem de sucesso ou erro")
    
    # Resposta completa da API
    raw_response = models.JSONField(null=True, blank=True,
                                   help_text="Resposta completa da API M-Pesa")
    
    # Metadados
    from_app = models.CharField(max_length=100, null=True, blank=True,
                               help_text="Aplicação de origem (ex: CartaFacil)")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Transação"
        verbose_name_plural = "Transações"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['customer_msisdn', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['transaction_reference']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.customer_msisdn} - {self.amount} MT ({self.status})"
    
    @property
    def is_successful(self):
        """Verifica se a transação foi bem-sucedida."""
        return self.status == 'success'
    
    @property
    def formatted_amount(self):
        """Retorna o valor formatado."""
        return f"{self.amount:,.2f} MT"
"""
URLs da API de pagamentos M-Pesa.
"""

from django.urls import path
from . import views

app_name = 'payments_mpesa'

urlpatterns = [
    # OAuth
    path('oauth/token', views.oauth_token, name='oauth_token'),
    
    # M-Pesa C2B
    path('v1/c2b/mpesa-payment/<int:wallet_id>', 
         views.mpesa_c2b_payment, 
         name='mpesa_c2b_payment'),
    
    # Relatórios
    path('transactions/list', 
         views.transactions_list, 
         name='transactions_list'),
    
    path('transactions/daily-report', 
         views.transactions_daily_report, 
         name='transactions_daily_report'),
    
    path('transactions/monthly-report', 
         views.transactions_monthly_report, 
         name='transactions_monthly_report'),
]
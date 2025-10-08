"""
URLs do aplicativo de pagamentos.
"""

from django.urls import path
from . import views

app_name = 'payments_mpesa'

urlpatterns = [
    path('c2b/', views.c2b_payment, name='c2b_payment'),
    path('b2c/', views.b2c_payment, name='b2c_payment'),

     # Endpoints de consulta
    path('transactions/', views.transactions_list, name='transactions_list'),
    path('transactions/daily/', views.transactions_daily_report, name='transactions_daily'),
    path('transactions/monthly/', views.transactions_monthly_report, name='transactions_monthly'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('initiate/', views.initiate_payment, name='initiate_payment'),  # Para PushMessage (C2B)
    path('disburse/', views.disburse, name='disburse'),  # Para Disbursement (B2C)
    path('check_status/', views.check_status, name='check_status'),  # Ver status de transação
    path('get_name/', views.get_beneficiary_name, name='get_name'),  # Obter nome do beneficiário
    path('check_balance/', views.check_balance, name='check_balance'),  # Ver saldo da conta
    path('callback/', views.callback, name='callback'),  # Para callbacks da eMola (async)
]
"""
Endpoints da API para transações C2B e B2C do M-Pesa com geração automática de referências.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from .mpesa import Mpesa
import json
import logging
import uuid
from datetime import datetime
from django.db import models


from .models import Transaction
from django.db.models import Sum, Count
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)

def generate_transaction_reference():
    """Gera uma referência de transação única para Mawonelo, com até 20 caracteres e sem símbolos."""
    prefix = "MAW"  # Prefixo da empresa Mawonelo
    timestamp = datetime.now().strftime("%m%d%H%M%S")  # Formato MMDDHHMMSS (10 caracteres)
    return f"{prefix}{timestamp}"  # Ex.: MAW0925150412 (13 caracteres)

def generate_third_party_reference():
    """Gera uma referência de terceiros usando UUID, sem hífens, com até 20 caracteres."""
    uuid_str = str(uuid.uuid4()).replace("-", "").upper()
    return uuid_str[:20]  # Limita a 20 caracteres para compatibilidade

@csrf_exempt
@require_POST
def c2b_payment(request):
    """Endpoint para processar pagamentos C2B com referências automáticas."""
    try:
        data = json.loads(request.body)
        customer_msisdn = data.get('customer_msisdn')
        amount = data.get('amount')
        transaction_reference = data.get('transaction_reference', generate_transaction_reference())
        third_party_reference = data.get('third_party_reference', generate_third_party_reference())
        service_provider_code = data.get('service_provider_code')

        if not all([customer_msisdn, amount]):
            logger.warning("Parâmetros obrigatórios ausentes na requisição C2B")
            return JsonResponse({'error': 'Parâmetros obrigatórios (customer_msisdn, amount) ausentes'}, status=400)

        # Valida o comprimento do transaction_reference
        if len(transaction_reference) > 20:
            logger.warning(f"transaction_reference muito longo: {transaction_reference}")
            return JsonResponse({'error': 'Referência de transação excede 20 caracteres'}, status=400)

        mpesa = Mpesa()
        response = mpesa.c2b(
            transaction_reference,
            customer_msisdn,
            amount,
            third_party_reference,
            service_provider_code
        )
        
        # Personaliza a resposta com base no sucesso ou falha
        if response.get('success', False):
            logger.info(f"Transação C2B bem-sucedida: {response['response']['output_TransactionID']}")
            # Dentro do if response.get('success', False):  (para salvar transação bem-sucedida)
            Transaction.objects.create(
                transaction_type="C2B",
                transaction_id=response['response'].get('output_TransactionID'),
                conversation_id=response['response'].get('output_ConversationID'),
                transaction_reference=transaction_reference,
                third_party_reference=third_party_reference,
                customer_msisdn=customer_msisdn,
                amount=amount,
                status='success',
                message=response['error_message'],
                raw_response=response['response']
            )
            return JsonResponse({
                'status': 'success',
                'transaction_id': response['response'].get('output_TransactionID'),
                'conversation_id': response['response'].get('output_ConversationID'),
                'third_party_reference': third_party_reference,
                'customer_msisdn': customer_msisdn,
                'amount': amount,
                'transaction_reference': transaction_reference,
                'message': response['error_message']
            }, status=response['status'])
        else:
            logger.error(f"Falha na transação C2B: {response['error_message']}")
            Transaction.objects.create(
                transaction_type="C2B",
                transaction_reference=transaction_reference,
                third_party_reference=third_party_reference,
                customer_msisdn=customer_msisdn,
                amount=amount,
                status='error',
                message=response['error_message'],
                raw_response=response['response']
            )
            return JsonResponse({
                'status': 'error',
                'message': response['error_message'],
                'response': response['response']
            }, status=response['status'] if response['status'] != 500 else 400)
    except Exception as e:
        logger.error(f"Erro no endpoint C2B: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_POST
def b2c_payment(request):
    """Endpoint para processar pagamentos B2C com referências automáticas."""
    try:
        data = json.loads(request.body)
        customer_msisdn = data.get('customer_msisdn')
        amount = data.get('amount')
        transaction_reference = data.get('transaction_reference', generate_transaction_reference())
        third_party_reference = data.get('third_party_reference', generate_third_party_reference())
        service_provider_code = data.get('service_provider_code')

        if not all([customer_msisdn, amount]):
            logger.warning("Parâmetros obrigatórios ausentes na requisição B2C")
            return JsonResponse({'error': 'Parâmetros obrigatórios (customer_msisdn, amount) ausentes'}, status=400)

        # Valida o comprimento do transaction_reference
        if len(transaction_reference) > 20:
            logger.warning(f"transaction_reference muito longo: {transaction_reference}")
            return JsonResponse({'error': 'Referência de transação excede 20 caracteres'}, status=400)

        mpesa = Mpesa()
        response = mpesa.b2c(
            transaction_reference,
            customer_msisdn,
            amount,
            third_party_reference,
            service_provider_code
        )
        
        # Personaliza a resposta com base no sucesso ou falha
        if response.get('success', False):
            logger.info(f"Transação B2C bem-sucedida: {response['response']['output_TransactionID']}")
            Transaction.objects.create(
                transaction_type="C2B",
                transaction_id=response['response'].get('output_TransactionID'),
                conversation_id=response['response'].get('output_ConversationID'),
                transaction_reference=transaction_reference,
                third_party_reference=third_party_reference,
                customer_msisdn=customer_msisdn,
                amount=amount,
                status='success',
                message=response['error_message'],
                raw_response=response['response']
            )
            return JsonResponse({
                'status': 'success',
                'transaction_id': response['response'].get('output_TransactionID'),
                'conversation_id': response['response'].get('output_ConversationID'),
                'third_party_reference': third_party_reference,
                'customer_msisdn': customer_msisdn,
                'amount': amount,
                'transaction_reference': transaction_reference,
                'message': response['error_message']
            }, status=response['status'])
        else:
            logger.error(f"Falha na transação B2C: {response['error_message']}")

            Transaction.objects.create(
                transaction_type="C2B",
                transaction_reference=transaction_reference,
                third_party_reference=third_party_reference,
                customer_msisdn=customer_msisdn,
                amount=amount,
                status='error',
                message=response['error_message'],
                raw_response=response['response']
            )

            return JsonResponse({
                'status': 'error',
                'message': response['error_message'],
                'response': response['response']
            }, status=response['status'] if response['status'] != 500 else 400)
    except Exception as e:
        logger.error(f"Erro no endpoint B2C: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    


# 🔹 Listar todas as transações ou filtrar por usuário
@require_GET
@csrf_exempt
def transactions_list(request):
    """
    Endpoint para listar transações.
    Suporta filtros: ?customer_msisdn=2588xxxxxxx&transaction_type=C2B
    """
    customer_msisdn = request.GET.get('customer_msisdn')
    transaction_type = request.GET.get('transaction_type')

    qs = Transaction.objects.all()

    if customer_msisdn:
        qs = qs.filter(customer_msisdn=customer_msisdn)
    if transaction_type:
        qs = qs.filter(transaction_type=transaction_type)

    data = [
        {
            "id": t.id,
            "transaction_type": t.transaction_type,
            "transaction_reference": t.transaction_reference,
            "third_party_reference": t.third_party_reference,
            "customer_msisdn": t.customer_msisdn,
            "amount": t.amount,
            "status": t.status,
            "message": t.message,
            "created_at": t.created_at,
        }
        for t in qs.order_by("-created_at")
    ]
    return JsonResponse({"transactions": data}, safe=False)


# 🔹 Estatísticas diárias
# 🔹 Estatísticas diárias
@require_GET
@csrf_exempt
def transactions_daily_report(request):
    """
    Relatório diário: total de transações bem-sucedidas, 
    soma de valores apenas das bem-sucedidas e número de erros.
    """
    today = datetime.today().date()
    qs = Transaction.objects.filter(created_at__date=today)

    # Somente as transações bem-sucedidas
    total_amount = qs.filter(status="success").aggregate(Sum("amount"))["amount__sum"] or 0
    total_success = qs.filter(status="success").count()
    total_errors = qs.filter(status="error").count()

    return JsonResponse({
        "date": str(today),
        "total_amount": total_amount,
        "total_success": total_success,
        "total_errors": total_errors
    })


# 🔹 Estatísticas mensais
@csrf_exempt
@require_GET
def transactions_monthly_report(request):
    """
    Relatório mensal: soma de valores e contagem de transações por dia.
    Apenas transações bem-sucedidas são somadas.
    """
    today = datetime.today()
    first_day = today.replace(day=1)

    qs = Transaction.objects.filter(created_at__gte=first_day)

    daily_stats = (
        qs.values("created_at__date")
        .annotate(
            total_amount=Sum("amount", filter=models.Q(status="success")),  # só sucessos
            total_success=Count("id", filter=models.Q(status="success")),
            total_errors=Count("id", filter=models.Q(status="error"))
        )
        .order_by("created_at__date")
    )

    return JsonResponse({"monthly_report": list(daily_stats)})

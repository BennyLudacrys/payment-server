"""
Endpoints da API adaptados para funcionar com o frontend Vuex/Quasar.
Suporta autenticação OAuth2 e processamento de pagamentos M-Pesa C2B.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from .mpesa import Mpesa
import json
import logging
import uuid
from datetime import datetime, timedelta
from django.db import models
from django.utils.decorators import method_decorator
from django.views import View

from .models import Transaction, OAuthToken
from django.db.models import Sum, Count

logger = logging.getLogger(__name__)


# ==================== FUNÇÕES AUXILIARES ====================

def generate_transaction_reference():
    """Gera uma referência de transação única para Mawonelo."""
    prefix = "MAW"
    timestamp = datetime.now().strftime("%m%d%H%M%S")
    return f"{prefix}{timestamp}"


def generate_third_party_reference():
    """Gera uma referência de terceiros usando UUID."""
    uuid_str = str(uuid.uuid4()).replace("-", "").upper()
    return uuid_str[:20]


def validate_bearer_token(request):
    """Valida o token Bearer enviado no header Authorization."""
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return False, "Token inválido ou ausente"
    
    token = auth_header.replace('Bearer ', '').strip()
    
    try:
        oauth_token = OAuthToken.objects.get(
            access_token=token,
            expires_at__gt=datetime.now()
        )
        return True, oauth_token
    except OAuthToken.DoesNotExist:
        return False, "Token expirado ou inválido"


# ==================== OAUTH TOKEN ENDPOINT ====================

@csrf_exempt
@require_POST
def oauth_token(request):
    """
    Endpoint de autenticação OAuth2.
    POST /oauth/token
    Body: {
        "grant_type": "client_credentials",
        "client_id": "a0140c9f-4c66-426e-beea-73bef5ac5023",
        "client_secret": "4lmO05AdGlnwmkrbDXDhm4eFTvxi5j0Sb8YsviVx"
    }
    """
    try:
        data = json.loads(request.body)
        
        grant_type = data.get('grant_type')
        client_id = data.get('client_id')
        client_secret = data.get('client_secret')
        
        # Validação dos campos obrigatórios
        if grant_type != 'client_credentials':
            return JsonResponse({'error': 'grant_type inválido'}, status=400)
        
        # Credenciais válidas (da carteira Mawonelo)
        VALID_CLIENT_ID = 'a0140c9f-4c66-426e-beea-73bef5ac5023'
        VALID_CLIENT_SECRET = '4lmO05AdGlnwmkrbDXDhm4eFTvxi5j0Sb8YsviVx'
        
        if client_id != VALID_CLIENT_ID or client_secret != VALID_CLIENT_SECRET:
            logger.warning(f"Tentativa de autenticação com credenciais inválidas: {client_id}")
            return JsonResponse({'error': 'Credenciais inválidas'}, status=401)
        
        # Gera token de acesso
        access_token = str(uuid.uuid4()).replace('-', '')
        expires_in = 3600  # 1 hora
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        # Salva o token no banco de dados
        OAuthToken.objects.create(
            client_id=client_id,
            access_token=access_token,
            token_type='Bearer',
            expires_at=expires_at,
            expires_in=expires_in
        )
        
        logger.info(f"Token OAuth gerado com sucesso para client_id: {client_id}")
        
        return JsonResponse({
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': expires_in
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Erro ao gerar token OAuth: {str(e)}")
        return JsonResponse({'error': 'Erro interno do servidor'}, status=500)


# ==================== MPESA C2B PAYMENT ENDPOINT ====================

@csrf_exempt
@require_POST
def mpesa_c2b_payment(request, wallet_id):
    """
    Endpoint para processar pagamentos M-Pesa C2B.
    POST /v1/c2b/mpesa-payment/{wallet_id}
    
    Headers:
        Authorization: Bearer {token}
        Content-Type: application/json
    
    Body: {
        "client_id": "a0140c9f-4c66-426e-beea-73bef5ac5023",
        "phone": "258840000000",
        "amount": "100",
        "reference": "CUSTOM_REF_123",
        "fromApp": "CartaFacil"
    }
    """
    try:
        # Valida o token
        is_valid, result = validate_bearer_token(request)
        if not is_valid:
            logger.warning(f"Tentativa de pagamento com token inválido: {result}")
            return JsonResponse({'error': result}, status=401)
        
        # Parse do body
        data = json.loads(request.body)
        
        client_id = data.get('client_id')
        phone = data.get('phone')
        amount = data.get('amount')
        reference = data.get('reference')
        from_app = data.get('fromApp', 'Unknown')
        
        # Validação dos campos obrigatórios
        if not all([client_id, phone, amount]):
            logger.warning("Parâmetros obrigatórios ausentes na requisição M-Pesa C2B")
            return JsonResponse({
                'error': 'Parâmetros obrigatórios ausentes',
                'required': ['client_id', 'phone', 'amount']
            }, status=400)
        
        # Valida o wallet_id
        VALID_WALLET_ID = 132722
        if int(wallet_id) != VALID_WALLET_ID:
            logger.warning(f"Wallet ID inválido: {wallet_id}")
            return JsonResponse({'error': 'Wallet ID inválido'}, status=400)
        
        # Normaliza o número de telefone (adiciona 258 se necessário)
        customer_msisdn = phone if phone.startswith('258') else f'258{phone}'
        
        # Gera referências se não fornecidas
        transaction_reference = reference or generate_transaction_reference()
        third_party_reference = generate_third_party_reference()
        
        # Valida o comprimento da referência
        if len(transaction_reference) > 20:
            logger.warning(f"transaction_reference muito longo: {transaction_reference}")
            return JsonResponse({'error': 'Referência excede 20 caracteres'}, status=400)
        
        logger.info(f"Processando pagamento M-Pesa C2B: {customer_msisdn}, {amount} MT, App: {from_app}")
        
        # Processa o pagamento via M-Pesa
        mpesa = Mpesa()
        response = mpesa.c2b(
            transaction_reference,
            customer_msisdn,
            amount,
            third_party_reference,
            service_provider_code=None  # Usa o padrão
        )
        
        # Salva a transação no banco de dados
        if response.get('success', False):
            logger.info(f"Transação M-Pesa C2B bem-sucedida: {response['response']['output_TransactionID']}")
            
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
                raw_response=response['response'],
                from_app=from_app
            )
            
            return JsonResponse({
                'success': True,
                'status': 'success',
                'transaction_id': response['response'].get('output_TransactionID'),
                'conversation_id': response['response'].get('output_ConversationID'),
                'third_party_reference': third_party_reference,
                'customer_msisdn': customer_msisdn,
                'amount': amount,
                'transaction_reference': transaction_reference,
                'message': response['error_message']
            }, status=200)
        else:
            logger.error(f"Falha na transação M-Pesa C2B: {response['error_message']}")
            
            Transaction.objects.create(
                transaction_type="C2B",
                transaction_reference=transaction_reference,
                third_party_reference=third_party_reference,
                customer_msisdn=customer_msisdn,
                amount=amount,
                status='error',
                message=response['error_message'],
                raw_response=response['response'],
                from_app=from_app
            )
            
            return JsonResponse({
                'success': False,
                'status': 'error',
                'message': response['error_message'],
                'response': response['response']
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Erro no endpoint M-Pesa C2B: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


# ==================== EMOLA C2B PAYMENT ENDPOINT ====================

@csrf_exempt
@require_POST
def emola_c2b_payment(request, wallet_id):
    """
    Endpoint para processar pagamentos eMola C2B.
    POST /v1/c2b/emola-payment/{wallet_id}
    
    Headers:
        Authorization: Bearer {token}
        Content-Type: application/json
    
    Body: {
        "client_id": "a0140c9f-4c66-426e-beea-73bef5ac5023",
        "phone": "258860000000",
        "amount": "100",
        "reference": "CUSTOM_REF_123"
    }
    """
    try:
        # Valida o token
        is_valid, result = validate_bearer_token(request)
        if not is_valid:
            logger.warning(f"Tentativa de pagamento eMola com token inválido: {result}")
            return JsonResponse({'error': result}, status=401)
        
        # Parse do body
        data = json.loads(request.body)
        
        client_id = data.get('client_id')
        phone = data.get('phone')
        amount = data.get('amount')
        reference = data.get('reference')
        
        # Validação dos campos obrigatórios
        if not all([client_id, phone, amount]):
            logger.warning("Parâmetros obrigatórios ausentes na requisição eMola C2B")
            return JsonResponse({
                'error': 'Parâmetros obrigatórios ausentes',
                'required': ['client_id', 'phone', 'amount']
            }, status=400)
        
        # Valida o wallet_id
        VALID_WALLET_ID = 989473  # Wallet ID para eMola
        if int(wallet_id) != VALID_WALLET_ID:
            logger.warning(f"Wallet ID eMola inválido: {wallet_id}")
            return JsonResponse({'error': 'Wallet ID inválido'}, status=400)
        
        # Normaliza o número de telefone
        customer_msisdn = phone if phone.startswith('258') else f'258{phone}'
        
        # Gera referências
        transaction_reference = reference or generate_transaction_reference()
        third_party_reference = generate_third_party_reference()
        
        logger.info(f"Processando pagamento eMola C2B: {customer_msisdn}, {amount} MT")
        
        # TODO: Implementar integração com eMola
        # Por enquanto, retorna sucesso simulado
        
        return JsonResponse({
            'success': True,
            'status': 'success',
            'message': 'Pagamento eMola processado com sucesso',
            'transaction_reference': transaction_reference,
            'customer_msisdn': customer_msisdn,
            'amount': amount
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Erro no endpoint eMola C2B: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


# ==================== ENDPOINTS DE RELATÓRIOS ====================

@require_GET
@csrf_exempt
def transactions_list(request):
    """Listar transações com filtros opcionais."""
    customer_msisdn = request.GET.get('customer_msisdn')
    transaction_type = request.GET.get('transaction_type')
    from_app = request.GET.get('from_app')

    qs = Transaction.objects.all()

    if customer_msisdn:
        qs = qs.filter(customer_msisdn=customer_msisdn)
    if transaction_type:
        qs = qs.filter(transaction_type=transaction_type)
    if from_app:
        qs = qs.filter(from_app=from_app)

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
            "from_app": t.from_app,
            "created_at": t.created_at.isoformat(),
        }
        for t in qs.order_by("-created_at")
    ]
    return JsonResponse({"transactions": data}, safe=False)


@require_GET
@csrf_exempt
def transactions_daily_report(request):
    """Relatório diário de transações."""
    today = datetime.today().date()
    qs = Transaction.objects.filter(created_at__date=today)

    total_amount = qs.filter(status="success").aggregate(Sum("amount"))["amount__sum"] or 0
    total_success = qs.filter(status="success").count()
    total_errors = qs.filter(status="error").count()

    return JsonResponse({
        "date": str(today),
        "total_amount": float(total_amount),
        "total_success": total_success,
        "total_errors": total_errors
    })


@csrf_exempt
@require_GET
def transactions_monthly_report(request):
    """Relatório mensal de transações."""
    today = datetime.today()
    first_day = today.replace(day=1)

    qs = Transaction.objects.filter(created_at__gte=first_day)

    daily_stats = (
        qs.values("created_at__date")
        .annotate(
            total_amount=Sum("amount", filter=models.Q(status="success")),
            total_success=Count("id", filter=models.Q(status="success")),
            total_errors=Count("id", filter=models.Q(status="error"))
        )
        .order_by("created_at__date")
    )

    return JsonResponse({"monthly_report": list(daily_stats)})

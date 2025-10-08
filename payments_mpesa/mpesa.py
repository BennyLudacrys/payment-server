"""
Implementação do serviço M-Pesa para transações C2B e B2C com third_party_reference estático.
"""

import base64
import requests
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Mapeamento de códigos de erro do M-Pesa
ERROR_CODES = {
    "INS-0": "Sucesso",
    "INS-6": "Saldo insuficiente",
    "INS-14": "PIN incorreto",
    "INS-9": "Timeout na transação",
    "INS-10": "Transação não encontrada",
    "INS-996": "Erro genérico no processamento",
    "INS-2006": "Saldo insuficiente"
}

class Mpesa:
    def __init__(self):
        """Inicializa o serviço M-Pesa com as configurações do Django."""
        self.config = settings.MPESA_CONFIG
        self.base_uri = 'https://api.sandbox.vm.co.mz' if self.config['ENV'] == 'sandbox' else 'https://api.vm.co.mz'
        self.public_key = self.config['PUBLIC_KEY']
        self.api_key = self.config['API_KEY']
        self.service_provider_code = self.config['SERVICE_PROVIDER_CODE']
        self.default_third_party_reference = self.config['THIRD_PARTY_REFERENCE']  # Valor estático padrão

    def _get_token(self):
        """Gera um token de autorização Bearer codificado em Base64."""
        try:
            # Formata a chave pública
            public_key = f"-----BEGIN PUBLIC KEY-----\n{self.public_key}\n-----END PUBLIC KEY-----"
            public_key_bytes = public_key.encode('utf-8')
            public_key_obj = serialization.load_pem_public_key(public_key_bytes, backend=default_backend())

            # Criptografa a API key
            encrypted = public_key_obj.encrypt(
                self.api_key.encode('utf-8'),
                padding.PKCS1v15()
            )
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"Erro ao gerar token: {str(e)}")
            return None

    def _get_headers(self):
        """Retorna os cabeçalhos para as requisições HTTP."""
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self._get_token()}',
            'Origin': 'developer.mpesa.vm.co.mz',
            'Connection': 'keep-alive'
        }

    def _make_request(self, url, port, method, data=None):
        """Faz uma requisição HTTP para a API M-Pesa e trata erros."""
        full_url = f"{self.base_uri}:{port}{url}"
        headers = self._get_headers()
        try:
            response = requests.request(
                method=method,
                url=full_url,
                headers=headers,
                json=data if method in ['POST', 'PUT'] else None,
                params=data if method == 'GET' else None,
                timeout=90,
                verify=False
            )
            result = {
                'status': response.status_code,
                'response': response.json() if response.text else None
            }
            # Tratar códigos de erro do M-Pesa
            if result['response'] and 'output_ResponseCode' in result['response']:
                response_code = result['response']['output_ResponseCode']
                result['error_message'] = ERROR_CODES.get(response_code, "Erro desconhecido")
                logger.info(f"Resposta M-Pesa: {response_code} - {result['error_message']}")
                if response_code != "INS-0":
                    result['success'] = False
                else:
                    result['success'] = True
            else:
                result['success'] = False
                result['error_message'] = "Resposta inválida da API M-Pesa"
                logger.error(f"Resposta inválida: {result['response']}")
            return result
        except Exception as e:
            logger.error(f"Erro na requisição para {url}: {str(e)}")
            return {'status': 500, 'response': None, 'success': False, 'error_message': str(e)}

    def c2b(self, transaction_reference, customer_msisdn, amount, third_party_reference=None, service_provider_code=None):
        """Inicia uma transação Customer to Business (C2B)."""
        service_provider_code = service_provider_code or self.service_provider_code
        third_party_reference = third_party_reference or self.default_third_party_reference  # Usa valor estático se não fornecido
        data = {
            "input_TransactionReference": transaction_reference,
            "input_CustomerMSISDN": customer_msisdn,
            "input_Amount": amount,
            "input_ThirdPartyReference": third_party_reference,
            "input_ServiceProviderCode": service_provider_code
        }
        logger.info(f"Iniciando transação C2B: {data}")
        return self._make_request('/ipg/v1x/c2bPayment/singleStage/', 18352, 'POST', data)

    def b2c(self, transaction_reference, customer_msisdn, amount, third_party_reference=None, service_provider_code=None):
        """Inicia uma transação Business to Customer (B2C)."""
        service_provider_code = service_provider_code or self.service_provider_code
        third_party_reference = third_party_reference or self.default_third_party_reference  # Usa valor estático se não fornecido
        data = {
            "input_TransactionReference": transaction_reference,
            "input_CustomerMSISDN": customer_msisdn,
            "input_Amount": amount,
            "input_ThirdPartyReference": third_party_reference,
            "input_ServiceProviderCode": service_provider_code
        }
        logger.info(f"Iniciando transação B2C: {data}")
        return self._make_request('/ipg/v1x/b2cPayment/', 18345, 'POST', data)
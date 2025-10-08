import uuid
import requests
import xml.etree.ElementTree as ET
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Transaction

# Função auxiliar para enviar requisição SOAP
# def send_soap_request(wscode, params):
#     username = settings.EMOLA_USERNAME
#     password = settings.EMOLA_PASSWORD
#     endpoint = settings.EMOLA_ENDPOINT

#     param_xml = ''
#     for name, value in params.items():
#         param_xml += f'<param name="{name}" value="{value}"/>'

#     body = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:web="http://webservice.bccsgw.viettel.com/">
#         <soapenv:Header/>
#         <soapenv:Body>
#             <web:gwOperation>
#                 <Input>
#                     <username>{username}</username>
#                     <password>{password}</password>
#                     <wscode>{wscode}</wscode>
#                     {param_xml}
#                     <rawData></rawData>
#                 </Input>
#             </web:gwOperation>
#         </soapenv:Body>
#     </soapenv:Envelope>"""

#     headers = {'Content-Type': 'text/xml; charset=utf-8'}
#     response = requests.post(endpoint, data=body, headers=headers)

#     if response.status_code != 200:
#         return {'error': 'HTTP error', 'code': response.status_code}

#     # Parse da resposta
#     try:
#         root = ET.fromstring(response.text)
#         ns = {'ns2': 'http://webservice.bccsgw.viettel.com/'}
#         error = root.find('.//ns2:Result/error', ns).text
#         description = root.find('.//ns2:Result/description', ns).text if root.find('.//ns2:Result/description', ns) is not None else ''
#         original = root.find('.//ns2:Result/original', ns).text if root.find('.//ns2:Result/original', ns) is not None else ''

#         if error != '0':
#             return {'error': error, 'description': description}

#         # Parse do XML interno se existir
#         if original:
#             inner_root = ET.fromstring(original)
#             inner_ns = {'ns2': 'http://services.wsfw.vas.viettel.com/'}
#             inner_error = inner_root.find('.//ns2:return/errorCode', inner_ns).text
#             inner_message = inner_root.find('.//ns2:return/message', inner_ns).text
#             request_id = inner_root.find('.//ns2:return/reqeustId', inner_ns).text if inner_root.find('.//ns2:return/reqeustId', inner_ns) is not None else ''
#             return {'errorCode': inner_error, 'message': inner_message, 'reqeustId': request_id}
#         return {'error': '0', 'description': description}
#     except Exception as e:
#         return {'error': 'Parse error', 'description': str(e)}
def send_soap_request(wscode, params):
    username = settings.EMOLA_USERNAME
    password = settings.EMOLA_PASSWORD
    endpoint = settings.EMOLA_ENDPOINT
    
    print(f"DEBUG - Credenciais:")
    print(f"Username: {'***' if username else 'MISSING'}")
    print(f"Password: {'***' if password else 'MISSING'}")
    print(f"Endpoint: {endpoint}")
    print(f"Partner Code: {settings.EMOLA_PARTNER_CODE}")
    print(f"Key: {'***' if settings.EMOLA_KEY else 'MISSING'}")
    print(f"WSCode: {wscode}")
    print(f"Params: {params}")

    param_xml = ''
    for name, value in params.items():
        param_xml += f'<param name="{name}" value="{value}"/>'

    body = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:web="http://webservice.bccsgw.viettel.com/">
        <soapenv:Header/>
        <soapenv:Body>
            <web:gwOperation>
                <Input>
                    <username>{username}</username>
                    <password>{password}</password>
                    <wscode>{wscode}</wscode>
                    {param_xml}
                    <rawData></rawData>
                </Input>
            </web:gwOperation>
        </soapenv:Body>
    </soapenv:Envelope>"""
    
    print(f"DEBUG - SOAP Request Body:")
    print(body)

    headers = {'Content-Type': 'text/xml; charset=utf-8'}
    
    try:
        response = requests.post(
            endpoint, 
            data=body, 
            headers=headers, 
            timeout=30,
            verify=False
        )
        
        print(f"DEBUG - Response Status: {response.status_code}")
        print(f"DEBUG - Response Content: {response.text}")
        
        if response.status_code != 200:
            return {'error': 'HTTP error', 'code': response.status_code, 'content': response.text}

        # Parse da resposta
        try:
            root = ET.fromstring(response.text)
            
            # Namespaces
            ns1 = {'S': 'http://schemas.xmlsoap.org/soap/envelope/'}
            ns2 = {'ns2': 'http://webservice.bccsgw.viettel.com/'}
            
            # Encontrar elementos
            result_elem = root.find('.//S:Body/ns2:gwOperationResponse/Result', {**ns1, **ns2})
            
            if result_elem is None:
                return {'error': 'Invalid response format', 'content': response.text}
                
            error_elem = result_elem.find('error')
            description_elem = result_elem.find('description')
            original_elem = result_elem.find('original')
            
            error = error_elem.text if error_elem is not None else 'UNKNOWN'
            description = description_elem.text if description_elem is not None else ''
            original = original_elem.text if original_elem is not None else ''

            print(f"DEBUG - Gateway Response: error={error}, description={description}")

            if error != '0':
                return {'error': error, 'description': description, 'gateway_error': True}

            # Parse do XML interno se existir
            if original and original.strip():
                try:
                    # Limpar CDATA se existir
                    clean_original = original.replace('<![CDATA[', '').replace(']]>', '').strip()
                    inner_root = ET.fromstring(clean_original)
                    
                    # Tentar diferentes namespaces para compatibilidade
                    inner_ns = {
                        'ns2': 'http://services.wsfw.vas.viettel.com/',
                        'S': 'http://schemas.xmlsoap.org/soap/envelope/'
                    }
                    
                    # Procurar o elemento return em diferentes locais
                    return_elem = None
                    for ns_prefix, ns_url in inner_ns.items():
                        return_elem = inner_root.find(f'.//{{{ns_url}}}return')
                        if return_elem is not None:
                            break
                    
                    if return_elem is not None:
                        error_code_elem = return_elem.find('errorCode')
                        message_elem = return_elem.find('message')
                        request_id_elem = return_elem.find('requestId')  # CORRIGIDO: era 'reqeustId'
                        
                        inner_error = error_code_elem.text if error_code_elem is not None else 'UNKNOWN'
                        inner_message = message_elem.text if message_elem is not None else ''
                        request_id = request_id_elem.text if request_id_elem is not None else ''
                        
                        print(f"DEBUG - API Response: errorCode={inner_error}, message={inner_message}, requestId={request_id}")
                        
                        return {
                            'errorCode': inner_error, 
                            'message': inner_message, 
                            'requestId': request_id,  # CORRIGIDO
                            'original': original
                        }
                    else:
                        return {'error': 'No return element found', 'original': original}
                        
                except Exception as inner_e:
                    print(f"DEBUG - Inner parse error: {str(inner_e)}")
                    return {'error': 'Inner parse error', 'description': str(inner_e), 'original': original}
            
            return {'error': '0', 'description': description}
            
        except Exception as parse_e:
            print(f"DEBUG - Parse error: {str(parse_e)}")
            return {'error': 'Parse error', 'description': str(parse_e), 'content': response.text}
            
    except requests.exceptions.ConnectionError as e:
        return {'error': 'Connection failed', 'description': str(e)}
    except requests.exceptions.Timeout as e:
        return {'error': 'Timeout', 'description': str(e)}
    except Exception as e:
        return {'error': 'Unexpected error', 'description': str(e)}
 
    
# View para iniciar pagamento (PushMessage - C2B)
# @csrf_exempt
# def initiate_payment(request):
#     if request.method != 'POST':
#         return HttpResponseBadRequest('Only POST allowed')
    
#     msisdn = request.POST.get('msisdn')
#     amount = request.POST.get('amount')
#     content = request.POST.get('content')
#     language = request.POST.get('language', 'pt')  # Padrão: Português
#     ref_no = request.POST.get('ref_no', '')

#     if not all([msisdn, amount, content]):
#         return JsonResponse({'error': 'Missing parameters'})

#     trans_id = str(uuid.uuid4())[:30]  # Gera transId único

#     params = {
#         'partnerCode': settings.EMOLA_PARTNER_CODE,
#         'msisdn': msisdn,
#         'smsContent': content,
#         'transAmount': amount,
#         'transId': trans_id,
#         'language': language,
#         'refNo': ref_no,
#         'key': settings.EMOLA_KEY,
#     }

#     result = send_soap_request('pushUssdMessage', params)

#     # Salva transação
#     txn = Transaction(trans_id=trans_id, msisdn=msisdn, amount=amount, content=content, ref_no=ref_no)
#     if 'errorCode' in result and result['errorCode'] == '0':
#         txn.status = 'success'
#         txn.request_id = result.get('reqeustId', '')
#     else:
#         txn.status = 'failed'
#     txn.save()

#     return JsonResponse(result)
# View para iniciar pagamento (PushMessage - C2B) - CORRIGIDA
@csrf_exempt
def initiate_payment(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Only POST allowed')
    
    msisdn = request.POST.get('msisdn')
    amount = request.POST.get('amount')
    content = request.POST.get('content')
    language = request.POST.get('language', 'pt')
    ref_no = request.POST.get('ref_no', '')

    if not all([msisdn, amount, content]):
        return JsonResponse({'error': 'Missing parameters'})

   
    if len(msisdn) == 9 and not msisdn.startswith(('86', '87')):
        # Adiciona prefixo padrão 86 se não tiver
        msisdn = '258' + msisdn

    trans_id = str(uuid.uuid4())[:30]

    params = {
        'partnerCode': settings.EMOLA_PARTNER_CODE,
        'msisdn': msisdn,
        'smsContent': content,
        'transAmount': amount,
        'transId': trans_id,
        'language': language,
        'refNo': ref_no,
        'key': settings.EMOLA_KEY,
    }

    # CORREÇÃO: WSCode correto
    result = send_soap_request('pushUsedMessage', params)

    # Salva transação
    txn = Transaction(
        trans_id=trans_id, 
        msisdn=msisdn, 
        amount=amount, 
        content=content, 
        ref_no=ref_no
    )
    
    if 'errorCode' in result and result['errorCode'] == '0':
        txn.status = 'pending'  # Mude para pending pois aguarda confirmação do usuário
        txn.request_id = result.get('requestId', '')  # CORRIGIDO
    else:
        txn.status = 'failed'
    txn.save()

    return JsonResponse(result)

# View para desembolso (B2C)
@csrf_exempt
def disburse(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Only POST allowed')
    
    msisdn = request.POST.get('msisdn')
    amount = request.POST.get('amount')
    content = request.POST.get('content', '')  # Opcional

    if not all([msisdn, amount]):
        return JsonResponse({'error': 'Missing parameters'})

    trans_id = str(uuid.uuid4())[:30]

    params = {
        'partnerCode': settings.EMOLA_PARTNER_CODE,
        'msisdn': msisdn,
        'smsContent': content,
        'transAmount': amount,
        'transId': trans_id,
        'key': settings.EMOLA_KEY,
    }

    result = send_soap_request('pushUsedDisbursementB2C', params)

    txn = Transaction(trans_id=trans_id, msisdn=msisdn, amount=amount, content=content)
    if 'errorCode' in result and result['errorCode'] == '0':
        txn.status = 'success'
        txn.request_id = result.get('reqeustId', '')
    else:
        txn.status = 'failed'
    txn.save()

    return JsonResponse(result)

# View para verificar status de transação
@csrf_exempt
def check_status(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Only POST allowed')
    
    trans_id = request.POST.get('trans_id')
    trans_type = request.POST.get('trans_type', 'C2B')  # Ex: C2B, B2C

    if not trans_id:
        return JsonResponse({'error': 'Missing trans_id'})

    params = {
        'partnerCode': settings.EMOLA_PARTNER_CODE,
        'transId': trans_id,
        'key': settings.EMOLA_KEY,
        'transType': trans_type,
    }

    result = send_soap_request('pushUsedQueryTrans', params)

    # Atualiza status local se necessário
    try:
        txn = Transaction.objects.get(trans_id=trans_id)
        if 'errorCode' in result and result['errorCode'] == '0':
            # Parse orgResponseCode
            if 'original' in result:
                inner_root = ET.fromstring(result['original'])
                inner_ns = {'ns2': 'http://services.wsfw.vas.viettel.com/'}
                org_code = inner_root.find('.//ns2:return/orgResponseCode', inner_ns).text
                txn.status = 'success' if org_code == '01' else 'failed'
                txn.save()
    except Transaction.DoesNotExist:
        pass

    return JsonResponse(result)

# View para obter nome do beneficiário
@csrf_exempt
def get_beneficiary_name(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Only POST allowed')
    
    msisdn = request.POST.get('msisdn')

    if not msisdn:
        return JsonResponse({'error': 'Missing msisdn'})

    trans_id = str(uuid.uuid4())[:30]

    params = {
        'partnerCode': settings.EMOLA_PARTNER_CODE,
        'msisdn': msisdn,
        'transId': trans_id,
        'key': settings.EMOLA_KEY,
    }

    result = send_soap_request('queryBeneficiaryName', params)

    # Extrai nome se sucesso
    if 'errorCode' in result and result['errorCode'] == '0':
        result['name'] = result['message']  # Como na doc: "A*** B***"

    return JsonResponse(result)

# View para verificar saldo da conta
@csrf_exempt
def check_balance(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Only POST allowed')
    
    # Nota: Pela doc, é para saldo do parceiro, sem msisdn
    trans_id = str(uuid.uuid4())[:30]

    params = {
        'partnerCode': settings.EMOLA_PARTNER_CODE,
        'transId': trans_id,
        'key': settings.EMOLA_KEY,
    }

    result = send_soap_request('queryAccountBalance', params)

    # Extrai saldo se sucesso
    if 'errorCode' in result and result['errorCode'] == '0':
        if 'original' in result:
            inner_root = ET.fromstring(result['original'])
            inner_ns = {'ns2': 'http://services.wsfw.vas.viettel.com/'}
            balance = inner_root.find('.//ns2:return/balance', inner_ns).text
            result['balance'] = balance

    return JsonResponse(result)

# View para callback (notificações async da eMola)
@csrf_exempt
def callback(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Only POST allowed')
    
    data = request.json()
    request_id = data.get('reqeustId')
    trans_id = data.get('transId')
    ref_no = data.get('refNo')
    error_code = data.get('errorCode')
    message = data.get('message')

    # Atualiza status da transação
    try:
        txn = Transaction.objects.get(trans_id=trans_id)
        txn.status = 'success' if error_code == '0' else 'failed'
        txn.request_id = request_id
        txn.save()
    except Transaction.DoesNotExist:
        pass  # Log se necessário

    # Responde conforme doc
    return JsonResponse({
        'ResponseCode': '0',
        'ResponseMessage': 'Callback received'
    })
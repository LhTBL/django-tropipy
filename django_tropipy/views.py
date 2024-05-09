import json
from django.conf import settings
from hashlib import sha1, sha256
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from tropipay.common import config_exists, get_config, ORDER_KEYS, get_payment_payload, perform_payment


def create_order(purchase_data, **kwargs):
    for key in ORDER_KEYS:
        if purchase_data.get(key) is None:
            return None
    return {key: purchase_data.get(key) for key in ORDER_KEYS}


@api_view(['POST'])
@csrf_exempt
def make_payment(request):
    if config_exists():
        tropipay_config = get_config()
        purchase_data = json.loads(request.body.decode('utf-8'))
        order = create_order(purchase_data, **{})
        if order is not None:
            return perform_payment(tropipay_config, get_payment_payload(tropipay_config, order))
    return Response(status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt)
def success(request):
    uuid: str = request.GET.get('reference').replace('-', '')
    if uuid is None:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    return redirect(
        f'https://api.whatsapp.com/send/?phone={settings.WHATSAPP_REDIRECT_PHONE}&text="Hello!, Just made the order with ticket {uuid}"&app_absent=1')


@method_decorator(csrf_exempt)
def verify(request):
    if request.method == 'POST':
        tropipay_config: dict = get_config()
        payload = json.loads(request.body)
        bankOrderCode = payload['data']['bankOrderCode']
        originalCurrencyAmount = payload['data']['originalCurrencyAmount']
        signature = payload['data']['signature']
        payload_status = payload['status']
        reference = payload['data']['reference']
        constructed_signature = sha256(
            f"{bankOrderCode}{tropipay_config.get("TROPIPAY_CLIENT_EMAIL")}{sha1(tropipay_config.get("TROPIPAY_CLIENT_PASSWORD").encode('utf-8')).hexdigest()}{originalCurrencyAmount}".encode(
                'utf-8')).hexdigest()
        if constructed_signature == signature:
            return Response(status=status.HTTP_200_OK, data={"reference": reference, "payload_status": payload_status})
    return Response(status=status.HTTP_400_BAD_REQUEST)

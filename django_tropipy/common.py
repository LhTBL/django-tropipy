from django.conf import settings
import http.client
import json
from urllib.parse import urlparse
import pytz
import datetime

from rest_framework import status
from rest_framework.response import Response

ACCESS_TOKEN_URL = "/api/v2/access/token"
PAYMENT_CARDS_URL = "/api/v2/paymentcards"

SETTINGS_VARIABLES = [
    'TROPIPAY_CLIENT_ID',
    'TROPIPAY_CLIENT_SECRET',
    'TROPIPAY_CLIENT_EMAIL',
    'TROPIPAY_CLIENT_PASSWORD',
    'TROPIPAY_URL',
    'TROPIPAY_SUCCESS_URL',
    'TROPIPAY_FAILED_URL',
    'TROPIPAY_NOTIFICATION_URL',
    'TROPIPAY_FEE',
    'TROPIPAY_TIMEZONE',
    'PAYMENT_CURRENCY',
]

ORDER_KEYS = [
    "uuid",
    "title",
    "name",
    "last_name",
    "email",
    "phone_number",
    "description",
    "location",
    "total"
]

def create_message_for_order(order):
    mensaje = [
        'Purchase via Tropipay:',
        f'Ticket: {order.get("uuid")}',
        f'Buyer: {order.get("name")} {order.get("last_name")}',
        f'Buyer Phone Numer: {order.get("phone_number")}',
        f'Buyer Email: {order.get("email")}',
        f'Total: {order.get("total"):.2f}USD',
        f'Location Details: {order.get("location")}',
        f'Other Details: {order.get("description")}'
    ]
    return '\n'.join(mensaje)

def config_exists():
    return not any(not hasattr(settings, variable) for variable in SETTINGS_VARIABLES)


def get_config():
    return {variable: getattr(settings, variable) for variable in SETTINGS_VARIABLES}


def get_token(tropipay_config):
    conn = http.client.HTTPSConnection(urlparse(tropipay_config.get("TROPIPAY_URL")).netloc)
    payload_tpp = json.dumps({
        "grant_type": "client_credentials",
        "client_id": tropipay_config.get("TROPIPAY_CLIENT_ID"),
        "client_secret": tropipay_config.get("TROPIPAY_CLIENT_SECRET")
    })
    conn.request("POST", ACCESS_TOKEN_URL, payload_tpp, {'Content-Type': "application/json"})
    return json.loads(conn.getresponse().read().decode("utf-8")).get("access_token")

def get_payment_payload(tropipay_config, order):
    time = datetime.datetime.now(pytz.timezone(tropipay_config.get("TROPIPAY_TIMEZONE")))
    fee = order.get("total") * tropipay_config.get("TROPIPAY_FEE") / 100
    return {
        "reference": order.get("uuid"),
        "concept": order.get("title"),
        "favorite": "false",
        "description": create_message_for_order(order),
        "amount": round(round((order.get("total") + fee + 0.5), 2) * 100) if fee > 0 else round(
            round(order.get("total"), 2) * 100),
        "currency": tropipay_config.get("PAYMENT_CURRENCY"),
        "singleUse": "true",
        "reasonId": 4,
        "expirationDays": 0,
        "lang": "es",
        "urlSuccess": tropipay_config.get("TROPIPAY_SUCCESS_URL"),
        "urlFailed": tropipay_config.get("TROPIPAY_FAILED_URL"),
        "urlNotification": tropipay_config.get("TROPIPAY_NOTIFICATION_URL"),
        "serviceDate": f"{time.year} - {time.month} - {time.day}",
        "client": {
            'name': order.get("name"),
            'lastName': order.get("last_name"),
            "address": order.get("location"),
            "phone": order.get("phone_number"),
            "email": order.get("email"),
            "countryId": 0,
            "termsAndConditions": "true"
        },
        "directPayment": "true",
        "paymentMethods": ["EXT", "TPP"]
    }

def perform_payment(tropipay_config, payload):
    conn = http.client.HTTPSConnection(urlparse(tropipay_config.get("TROPIPAY_URL")).netloc)
    token = get_token(tropipay_config)
    conn.request("POST", PAYMENT_CARDS_URL, json.dumps(payload), {
        'Content-Type': "application/json",
        'Authorization': "Bearer " + token
    })
    response = json.loads(conn.getresponse().read().decode("utf-8"))
    if 'error' in response:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(data={'payment_link': response.get('shortUrl', None)}, status=status.HTTP_200_OK)
import json

from django.conf import settings

from django.urls import reverse
from rest_framework import status

from tropipay.views import make_payment
from rest_framework.test import APIClient, APITestCase
from django.core.management import call_command
import environ
from django.contrib.auth import get_user_model
from model_bakery import baker, random_gen


class BaseTestCase(APITestCase):
    @staticmethod
    def get_base_url() -> str:
        return settings.BASE_URL


    @staticmethod
    def get_root_dir() -> str:
        import os
        env = environ.Env()
        return "./"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):

        super().setUp()
        self.client = APIClient()

        if self.fixtures:
            call_command(
                "loaddata_custom",
                *self.fixtures,
                **{"verbosity": 0, "schema": "test"},
            )

        self.user = get_user_model().objects.create_user(
            username="test",
            email=baker.random_gen.gen_email().lower(),
            password="pass",
            is_staff=True,
            is_superuser=True,
        )


class TestPayment(BaseTestCase):
    def test_make_payment(self):
        url = f"{self.get_base_url()}/tropipay/pay/"
        data = {
            "uuid":"test_uuid",
            "title":"Test Title",
            "name":"Test Name",
            "last_name":"Test Last Name",
            "email":"blinit10@gmail.com",
            "phone_number":"+535235131",
            "description":"Test Description",
            "location":"Test Location",
            "total": 30.00,

        }
        response = self.client.post(url, data, format="json")
        self.assertIsNotNone(response.json().get("payment_link"))

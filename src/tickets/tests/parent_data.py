from django.conf import settings as django_settings
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from tickets.models import *
from tickets.common.utils import get_hash_password
from tickets.common.actions import generate_keys
from tickets.management.commands.start_ticket_server import start_ticket_server


@override_settings(
    BROKER_BACKEND='memory',
    CELERY_TASK_EAGER_PROPAGATES=True,
    CELERY_TASK_ALWAYS_EAGER=True,
    PRIVATE_KEY_FILENAME='test_private.pem',
    PUBLIC_KEY_FILENAME='test_public.pem',
    KEY_PATH='tickets/tests/data/keys',
    CSV_PATH='tickets/tests/data/csv',
    QR_PATH='tickets/tests/data/codes'
)
class ParentTestDataMixin(TestCase):
    def setUp(self):
        """
        Создает администратора, продавца и контроллёра.
        Авторизует каждого из них,
        чтобы в каждом тесте было три подключения.
        self.admin
        self.agent
        self.carrier
        self.seller
        self.inspector
        """
        start_ticket_server()
        self.admin = APIClient()
        password = get_hash_password(django_settings.ADMIN_PASSWORD)
        response = self.admin.post('/api/login', {
            'login': settings.ADMIN_USER,
            'password': password
        }, format='json')
        assert response.status_code == 200
        access_token = response.data['access_token']
        self.admin.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)
        response = self.admin.post('/api/agents', {
            'company': {
                'inn': '7800000000'
            },
            'user': {
                'code': 666
            }
        }, format='json')
        assert response.status_code == 201

        password = response.data['password']
        login = response.data['login']

        self.agent = APIClient()
        response = self.agent.post('/api/login', {
            'login': login,
            'password': get_hash_password(password)
        }, format='json')
        assert response.status_code == 200
        access_token = response.data['access_token']
        self.agent.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)
        vehicle_type_ids = list(VehicleType.objects.values_list('id', flat=3))
        response = self.admin.post('/api/carriers', {
            'company': {
                'inn': '7830000001',
                'code': 777,
                'vehicle_types': vehicle_type_ids
            },
            'user': {
                'code': 888
            }
        }, format='json')

        assert response.status_code == 201
        password = response.data['password']
        login = response.data['login']

        self.carrier = APIClient()
        response = self.carrier.post('/api/login', {
            'login': login,
            'password': get_hash_password(password)
        }, format='json')
        assert response.status_code == 200
        access_token = response.data['access_token']
        self.carrier.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)


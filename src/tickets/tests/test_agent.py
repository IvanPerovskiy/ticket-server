import csv

from rest_framework.test import APIClient

from tickets.tests.parent_data import ParentTestDataMixin
from tickets.common.utils import b64d, b64e, get_hash_password
from tickets.models import *


class AdminTests(ParentTestDataMixin):

    def setUp(self):
        super().setUp()

    def create_inspector(self):
        response = self.carrier.post('/api/inspectors', {
            'code': 22222,
            'login': 'test_inspector',
            'name': 'Вася Петров',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        password = response.data['password']
        login = response.data['login']
        company = Company.objects.filter(
            inn='7830000001'
        ).first()
        inspector = User.objects.filter(
            role=UserRole.INSPECTOR,
            company=company
        ).first()
        self.assertEqual(inspector.login, 'test_inspector')
        self.assertEqual(inspector.name, 'Вася Петров')
        self.assertEqual(inspector.address, None)
        self.assertEqual(inspector.status, UserStatus.ACTIVE)
        self.inspector = APIClient()
        response = self.inspector.post('/api/login', {
            'login': login,
            'password': get_hash_password(password)
        }, format='json')
        assert response.status_code == 200
        access_token = response.data['access_token']
        self.inspector.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

    def create_validator(self):
        response = self.carrier.post('/api/validators', {
            'code': 333333,
            'login': 'test_validator',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        password = response.data['password']
        login = response.data['login']
        company = Company.objects.filter(
            inn='7830000001'
        ).first()
        validator = User.objects.filter(
            role=UserRole.VALIDATOR,
            company=company
        ).first()
        self.assertEqual(validator.login, 'test_validator')
        self.assertEqual(validator.name, None)
        self.assertEqual(validator.address, None)
        self.assertEqual(validator.status, UserStatus.ACTIVE)
        self.validator = APIClient()
        response = self.validator.post('/api/login', {
            'login': login,
            'password': get_hash_password(password)
        }, format='json')
        assert response.status_code == 200
        access_token = response.data['access_token']
        self.validator.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)
        return validator

    def create_seller(self):
        response = self.agent.post('/api/sellers', {
            'code': 11111,
            'login': 'test_seller',
            'name': 'Кассир 1',
            'address': 'Невский пр. 100'
        }, format='json')
        self.assertEqual(response.status_code, 201)
        password = response.data['password']
        login = response.data['login']
        company = Company.objects.filter(
            inn='7800000000'
        ).first()
        seller = User.objects.filter(
            role=UserRole.SELLER,
            company=company
        ).first()
        self.assertEqual(seller.login, 'test_seller')
        self.assertEqual(seller.name, 'Кассир 1')
        self.assertEqual(seller.address, 'Невский пр. 100')
        self.assertEqual(seller.status, UserStatus.ACTIVE)

        self.seller = APIClient()
        response = self.seller.post('/api/login', {
            'login': login,
            'password': get_hash_password(password)
        }, format='json')
        assert response.status_code == 200
        access_token = response.data['access_token']
        self.seller.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

    def create_sellers(self):
        agent_company = Company.objects.get(inn='7800000000')
        with open('tickets/tests/data/csv/sellers.csv', 'r', encoding='utf-8') as file:
            body = b64e(file.read())
        response = self.admin.post('/api/sellers/csv', {
            'company_id': agent_company.id,
            'file': body
        }, format='json')
        self.assertEqual(response.status_code, 201)
        tokens_body = b64d(response.data['file'])
        with open('tickets/tests/data/csv/seller_login.csv', 'w', newline='', encoding='utf-8') as content:
            content.write(tokens_body)

        with open('tickets/tests/data/csv/seller_login.csv', 'r', newline='', encoding='utf-8') as csv_file:
            i = 0
            for row in csv.DictReader(csv_file):
                i += 1
                setattr(self, 'seller_' + str(i), APIClient())
                seller = getattr(self, 'seller_' + str(i))
                password = row['password']
                login = row['login']

                response = seller.post('/api/login', {
                    'login': login,
                    'password': get_hash_password(password)
                }, format='json')
                self.assertEqual(response.status_code, 200)
                access_token = response.data['access_token']
                seller.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

    def test_tickets(self):
        self.create_seller()
        self.create_sellers()
        self.create_inspector()
        validator = self.create_validator()

        response = self.seller.post('/api/tickets', {
            'token': 'test_token'
        }, format='json')
        self.assertEqual(response.status_code, 201)
        ticket = Ticket.objects.latest('created')

        response = self.seller.post('/api/tickets', {
            'token': 'test_token'
        }, format='json')
        self.assertEqual(response.status_code, 201)
        ticket = Ticket.objects.latest('created')

        response = self.inspector.post('/api/tickets/trip')
        self.assertEqual(response.status_code, 403)

        response = self.validator.post('/api/tickets/trip',  {
            'ticket_id': ticket.id,
            'run_number': '560',
            'created': '2021-06-01 00:00',
            'validator_number': '8888',
            'route_number': '560dd',
            'vehicle_type': 1,
            'vehicle_number': '888338'
        }, format='json')

        self.assertEqual(response.status_code, 400)
        pub_key = 'Test pub key'
        response = self.validator.post('/api/workdays/open')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(validator.current_workday.id, response.data['workday_id'])
        workday_id = response.data['workday_id']
        response = self.validator.post('/api/tickets/trip',  {
            'ticket_id': ticket.id,
            'run_number': '560',
            'created': '2021-06-01 00:00',
            'validator_number': '8888',
            'route_number': '560dd',
            'vehicle_type': 1,
            'vehicle_number': '888338'
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 601)

        response = self.validator.post('/api/tickets/trip', {
            'ticket_id': ticket.id,
            'job_number': 1,
            'run_number': '560',
            'created': '2021-06-01 00:00',
            'validator_number': '8888',
            'route_number': '560dd',
            'vehicle_type': 1,
            'vehicle_number': '888338'
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 602)

        response = self.inspector.post('/api/tickets/trip', {
            'ticket_id': ticket.id,
            'vehicle_number': 555,
            'carrier_code': 5678
        }, format='json')
        self.assertEqual(response.status_code, 403)

        response = self.inspector.post('/api/tickets/check', {
            'ticket_id': ticket.id,
            'validator_number': '8888',
            'route_number': '560dd',
            'vehicle_type': 1,
            'vehicle_number': '888338',
            'carrier_code': 777
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 602)

        response = self.inspector.post('/api/tickets/check', {
            'ticket_id': ticket.id,
            'vehicle_number': 556,
            'carrier_code': 5678
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 603)

        response = self.seller.post('/api/tickets', {
            'token': 'test_token_1'
        }, format='json')
        first_ticket = Ticket.objects.latest('created')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(first_ticket.operations.all()), 0)

        response = self.seller.post('/api/tickets', {
            'token': 'test_token_2'
        }, format='json')
        second_ticket = Ticket.objects.latest('created')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(second_ticket.operations.all()), 0)

        response = self.seller.post('/api/tickets', {
            'token': 'test_token_3'
        }, format='json')
        third_ticket = Ticket.objects.latest('created')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(third_ticket.operations.all()), 0)

        response = self.validator.post('/api/tickets/load-trips', {
            'tickets': [
                {
                    'ticket_id': first_ticket.id,
                    'run_number': '560',
                    'created': '2021-06-01 00:00',
                    'validator_number': '8888',
                    'route_number': '560dd',
                    'vehicle_type': 1,
                    'vehicle_number': '888338'
                },
                {
                    'ticket_id': second_ticket.id,
                    'run_number': '560',
                    'created': '2021-06-01 00:00',
                    'validator_number': '8888',
                    'route_number': '560dd',
                    'vehicle_type': 1,
                    'vehicle_number': '888338'
                },
                {
                    'ticket_id': third_ticket.id,
                    'run_number': '560',
                    'created': '2021-06-01 00:00',
                    'validator_number': '8888',
                    'route_number': '560dd',
                    'vehicle_type': 1,
                    'vehicle_number': '888338'
                }
            ]}, format='json')
        self.assertEqual(response.status_code, 200)
        third_ticket.refresh_from_db()
        self.assertEqual(len(third_ticket.operations.all()), 1)
        self.assertEqual(third_ticket.status, TicketStatus.COMPLETED)

        response = self.validator.post('/api/workdays/{}/close'.format(workday_id))
        self.assertEqual(response.status_code, 400)
        response = self.validator.post('/api/workdays/{}/close'.format(workday_id), {
            'tickets': [
                {
                    'ticket_id': first_ticket.id,
                    'run_number': '560',
                    'created': '2021-06-01 00:00',
                    'validator_number': '8888',
                    'route_number': '560dd',
                    'vehicle_type': 1,
                    'vehicle_number': '888338'
                },
                {
                    'ticket_id': second_ticket.id,
                    'run_number': '560',
                    'created': '2021-06-01 00:00',
                    'validator_number': '8888',
                    'route_number': '560dd',
                    'vehicle_type': 1,
                    'vehicle_number': '888338'
                },
                {
                    'ticket_id': third_ticket.id,
                    'run_number': '560',
                    'created': '2021-06-01 00:00',
                    'validator_number': '8888',
                    'route_number': '560dd',
                    'vehicle_type': 1,
                    'vehicle_number': '888338'
                }
            ]}, format='json')
        self.assertEqual(response.status_code, 200)
        workday = Workday.objects.get(id=workday_id)
        self.assertEqual(workday.status, WorkdayStatus.CLOSED)
        self.assertEqual(validator.current_workday, None)


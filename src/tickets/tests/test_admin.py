import csv

from decimal import Decimal

from rest_framework.test import APIClient

from tickets.tests.parent_data import ParentTestDataMixin
from tickets.common.utils import b64d, b64e
from tickets.common.utils import get_hash_password
from tickets.models import *


class AdminTests(ParentTestDataMixin):

    def setUp(self):
        super().setUp()

    def create_tariff(self):
        response = self.admin.post('/api/tariffs', {
            'name': 'Тестовый_1',
            'cost': '100.00',
            'number': 10
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.first_tariff = Tariff.objects.get(id=response.data['id'])
        self.assertEqual(self.first_tariff.number, 10)

        response = self.admin.get('/api/tariffs/{}'.format(self.first_tariff.id))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['name'], 'Тестовый_1')

        response = self.admin.get('/api/tariffs?name=Тестовый_1')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data[0]['number'], 10)

        response = self.admin.post('/api/tariffs', {
            'name': 'Тестовый_2',
            'cost': '200.00',
            'number': 11
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.second_tariff = Tariff.objects.get(id=response.data['id'])
        self.assertEqual(self.second_tariff.number, 11)

        response = self.admin.get('/api/tariffs/{}'.format(self.second_tariff.id))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['name'], 'Тестовый_2')

        response = self.admin.get('/api/tariffs?name=Тестовый_2')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data[0]['number'], 11)

    def update_tariff(self):
        response = self.admin.put('/api/tariffs/{}'.format(self.first_tariff.id), {
            'name': 'Тестовый тариф 1',
            'cost': '120.00',
            'number': 11
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.first_tariff.refresh_from_db()
        first_tariff = Tariff.objects.get(id=response.data['id'])
        self.assertEqual(self.first_tariff.id, first_tariff.id)
        self.assertEqual(self.first_tariff.number, 10)
        self.assertEqual(self.first_tariff.cost, Decimal('120.00'))

        response = self.admin.get('/api/tariffs/{}'.format(first_tariff.id))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['name'], 'Тестовый тариф 1')
        self.assertEqual(response.data['number'], 10)
        return first_tariff

    def create_ticket_type(self):
        response = self.admin.post('/api/ticket-types', {
            'name': 'Тестовый_тип_1',
            'number': 20,
            'tariff': self.first_tariff.id,
            'zone': Zone.objects.first().id,
            'code': '979797',
            'lifetime': 30,
            'vehicle_types': [1, 2],
            'agent_permission': True
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.first_ticket_type = TicketType.objects.get(id=response.data['id'])
        self.assertEqual(self.first_ticket_type.number, 20)

        response = self.admin.get('/api/ticket-types/{}'.format(self.first_ticket_type.id))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['name'], 'Тестовый_тип_1')

        response = self.admin.get('/api/ticket-types?name=Тестовый_тип_1')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data[0]['number'], 20)

    def update_ticket_type(self):
        response = self.admin.put('/api/ticket-types/{}'.format(self.first_ticket_type.id), {
            'name': 'Тестовый_тип_2',
            'lifetime': 30,
            'vehicle_types': [1, 2],
            'agent_permission': True
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.first_ticket_type.refresh_from_db()
        self.assertEqual(self.first_ticket_type.name, 'Тестовый_тип_2')

        response = self.admin.get('/api/ticket-types/{}'.format(self.first_ticket_type.id))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['name'], 'Тестовый_тип_2')

        response = self.admin.get('/api/ticket-types?name=Тестовый_тип_1')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.data), 0)
        return self.first_ticket_type

    def update_status(self):
        response = self.admin.put('/api/ticket-types/{}/update-status'.format(self.first_ticket_type.id), {
            'status': 3
        }, format='json')
        self.assertEqual(response.status_code, 200)
        first_ticket_type = TicketType.objects.get(id=response.data['id'])
        self.assertEqual(first_ticket_type.name, 'Тестовый_тип_2')
        self.assertEqual(first_ticket_type.status, TicketTypeStatus.DISABLED)
        self.assertEqual(first_ticket_type.id, self.first_ticket_type.id)

        response = self.admin.get('/api/ticket-types/{}'.format(first_ticket_type.id))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['name'], 'Тестовый_тип_2')

        response = self.admin.get('/api/ticket-types?name=Тестовый_тип_1')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.data), 0)
        return first_ticket_type

    def create_agent(self):
        response = self.admin.post('/api/agents', {
            'company': {
                'inn': '7800000000',
                'code': 789,
                'name': 'Первый агент',
                'ticket_types': [self.first_ticket_type.id, ]
            },
            'user': {
                'code': 88888,
                'login': 'agent@agent.ru',
                'name': 'Главный пользователь агента',
                'address': 'Невский пр. 100',
                'password': 'tttt'
            }
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.agent_company = Company.objects.get(id=response.data['company_id'])
        self.agent_user = User.objects.get(id=response.data['user_id'])
        self.assertEqual(self.agent_user.company, self.agent_company)
        self.assertEqual(self.agent_company.category, CompanyCategory.AGENT)
        self.assertEqual(self.agent_user.role, UserRole.AGENT)
        login = response.data['login']

        self.new_agent = APIClient()
        response = self.new_agent.post('/api/login', {
            'login': login,
            'password': get_hash_password('tttt')
        }, format='json')
        self.assertEqual(response.status_code, 200)

        response = self.admin.post('/api/agents', {
            'company': {
                'inn': '7800000000',
                'code': 789,
                'name': 'Первый агент',
                'ticket_types': [self.first_ticket_type.id, ]
            },
            'user': {
                'code': 88888,
                'login': 'second_agent@agent.ru',
                'name': 'Главный пользователь второго агента',
                'address': 'Невский пр. 101'
            }
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.second_agent_company = Company.objects.get(id=response.data['company_id'])
        self.second_agent_user = User.objects.get(id=response.data['user_id'])
        self.assertEqual(self.agent_user.company, self.agent_company)
        self.assertEqual(self.agent_company.category, CompanyCategory.AGENT)
        self.assertEqual(self.agent_user.role, UserRole.AGENT)

        password = response.data['password']
        login = response.data['login']

        self.second_agent = APIClient()
        response = self.second_agent.post('/api/login', {
            'login': login,
            'password': get_hash_password(password)
        }, format='json')
        self.assertEqual(response.status_code, 200)

    def update_agent(self):
        response = self.admin.put('/api/agents/{}'.format(self.second_agent_company.id), {
            'name': 'Рога и копыта',
            'code': 790,
            'company_form': 'ООО',
            'secop_id': '1000',
            'short_name': 'РиК',
            'director': 'Иванов Иван Иванович',
            'position': 'генеральный директор',
            'sign_doc': 'Устав',
            'ogrn': '784444444444',
            'kpp': '780101001',
            'registration_address': 'Невский пр. 101',
            'actual_address': 'Невский пр. 101',
            'correspondence_address': 'Невский пр. 101',
            'bic': '044525225',
            'bank': 'СБЕР',
            'correspondent_account': '443435435135',
            'account': '65443534354354',
            'agent_fee': 20,
            'agent_fee_percent': True,
            'service_fee': 20,
            'service_fee_percent': True
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.second_agent_company.refresh_from_db()
        self.assertEqual(self.second_agent_company.short_name, 'РиК')

    def update_status_agent(self):
        response = self.admin.put('/api/agents/{}/update-status'.format(self.second_agent_company.id), {
            'status': CompanyStatus.DELETED
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.second_agent_company.refresh_from_db()

        self.assertEqual(self.second_agent_company.status, CompanyStatus.DELETED)

    def update_status_seller(self):
        pass

    def refresh_password_agent(self):
        response = self.admin.put('/api/refresh-password'.format(self.second_agent_company.id), {
            'user_id':  self.second_agent_user.id
        }, format='json')
        self.assertEqual(response.status_code, 200)
        password = response.data['password']
        login = response.data['login']

        response = self.second_agent.post('/api/login', {
            'login': login,
            'password': get_hash_password(password)
        }, format='json')
        self.assertEqual(response.status_code, 200)

    def create_route(self):
        pass

    def update_route(self):
        pass

    def create_carrier(self):
        pass

    def update_carrier(self):
        pass

    def refresh_password_carrier(self):
        pass

    def update_status_carrier(self):
        pass

    def load_inspectors(self):
        pass

    def create_inspector(self):
        pass

    def update_status_inspector(self):
        pass

    def test_admin_usecases(self):
        self.create_tariff()
        self.update_tariff()
        self.create_ticket_type()
        self.update_ticket_type()
        self.update_status()
        self.create_agent()
        self.update_agent()
        self.update_status_agent()
        self.refresh_password_agent()

    '''def test_admin(self):
        response = self.admin.get('/api/settings')
        self.assertEqual(response.status_code, 200)

        response = self.admin.put('/api/settings/',  {
            'ticket_cost': 56
        }, format='json')

        with open('tickets/tests/data/sellers.csv', encoding='utf-8') as file:
            body = b64e(file.read())
        response = self.admin.post('/api/agents/load', {
            'file': body
        }, format='json')
        self.assertEqual(response.status_code, 201)
        tokens_body = b64d(response.data['file'])

        with open('tickets/tests/data/seller_token.csv', 'w', newline='', encoding='utf-8') as content:
            content.write(tokens_body)

        with open('tickets/tests/data/seller_token.csv', 'r', newline='', encoding='utf-8') as csv_file:
            i = 0
            for row in csv.DictReader(csv_file):
                i += 1
                setattr(self, 'seller_'+str(i), APIClient())
                seller = getattr(self, 'seller_'+str(i))
                seller.credentials(HTTP_AUTHORIZATION='Bearer %s' % row['token'])

        response = self.seller_1.post('/api/tickets')
        ticket = Ticket.objects.latest('created')
        self.assertEqual(response.status_code, 201)

        with open('tickets/tests/data/inspectors.csv', encoding='utf-8') as file:
            body = b64e(file.read())
        response = self.admin.post('/api/carriers', {
            'file': body
        }, format='json')
        self.assertEqual(response.status_code, 201)
        tokens_body = b64d(response.data['file'])

        with open('tickets/tests/data/inspectors_token.csv', 'w', newline='', encoding='utf-8') as content:
            content.write(tokens_body)

        with open('tickets/tests/data/inspectors_token.csv', 'r', newline='', encoding='utf-8') as csv_file:
            i = 0
            for row in csv.DictReader(csv_file):
                i += 1
                setattr(self, 'inspector_'+str(i), APIClient())
                inspector = getattr(self, 'inspector_'+str(i))
                inspector.credentials(HTTP_AUTHORIZATION='Bearer %s' % row['token'])

        response = self.inspector_1.post('/api/tickets/trip')

        self.assertEqual(response.status_code, 400)

        response = self.inspector_1.post('/api/tickets/trip',  {
            'ticket_id': ticket.id,
            'vehicle_number': 555,
            'carrier_code': 5678
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 601)

        response = self.inspector_1.post('/api/tickets/trip', {
            'ticket_id': ticket.id,
            'vehicle_number': 555,
            'carrier_code': 5678
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 602)

        response = self.seller_1.post('/api/tickets/trip', {
            'ticket_id': ticket.id,
            'vehicle_number': 555,
            'carrier_code': 5678
        }, format='json')
        self.assertEqual(response.status_code, 403)

        response = self.inspector_1.post('/api/tickets/check', {
            'ticket_id': ticket.id,
            'vehicle_number': 555,
            'carrier_code': 5678
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 602)

        response = self.inspector_1.post('/api/tickets/check', {
            'ticket_id': ticket.id,
            'vehicle_number': 556,
            'carrier_code': 5678
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 603)'''


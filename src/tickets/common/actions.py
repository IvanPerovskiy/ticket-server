"""
Created on 24.08.2021

:author: Ivan Perovsky
Содержит различные сценарии для работы с БД
"""
import uuid
import json

from Crypto.PublicKey import RSA

from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model

from rest_framework.authtoken.models import Token
from django.core.management.utils import get_random_secret_key, get_random_string

from tickets.common.utils import get_hash_password
from tickets.models import UserRole, UserStatus, User, TicketType, Ticket, VehicleType, \
    Operation, TicketStatus, Company, CompanyStatus, CompanyCategory, TicketNumber, Device, \
    DeviceType, Workday


def create_auth_user(uuid_number=None):
    if not uuid_number:
        uuid_number = uuid.uuid4()
    auth_user = get_user_model().objects.create_user(
        uuid_number,
        is_active=True
    )
    return auth_user


def create_user(
        company,
        user_dict,
        role,
        password
):
    """
    Создает клиента и его пользователя
    """
    auth_user = create_auth_user(
        uuid.uuid4()
    )
    user = User.objects.create(
        id=auth_user.username,
        auth_user=auth_user,
        login=user_dict.get('login', str(user_dict.get('code', auth_user.username))),
        name=user_dict.get('name'),
        role=role,
        salt=get_random_secret_key(),
        status=UserStatus.ACTIVE,
        address=user_dict.get('address'),
        company=company,
        code=user_dict['code']
    )

    auth_user.set_password(user.hash_password(password))
    auth_user.save()
    return user


def refresh_password(user):
    new_password = get_random_string()
    password = get_hash_password(new_password)
    user.auth_user.set_password(user.hash_password(password))
    user.auth_user.save()
    return new_password


def create_admin_user(login, password):
    auth_user = create_auth_user(
        uuid.uuid4()
    )
    user = User.objects.create(
        id=auth_user.username,
        auth_user=auth_user,
        login=login,
        role=UserRole.ADMIN,
        salt=get_random_secret_key(),
        status=UserStatus.ACTIVE
    )

    auth_user.set_password(user.hash_password(password))
    auth_user.save()

    return user


def add_ticket_types_for_agent(company, ticket_type_ids=None):
    """
    Обновляет сведения о разрешенных типах билетов для продажи агентом
    """
    if ticket_type_ids:
        ticket_types = TicketType.objects.filter(
            id__in=ticket_type_ids
        ).values_list('id', flat=True)
    else:
        ticket_types = TicketType.objects.values_list('id', flat=True)

    for ticket_type in ticket_types:
        company.ticket_types.add(ticket_type)
    company.save()
    ticket_types = set(ticket_types)
    company_ticket_types = set(company.ticket_types.all())
    for ticket_type in company_ticket_types.difference(ticket_types):
        company.ticket_types.remove(ticket_type)


def add_vehicle_types_for_carrier(company, vehicle_type_ids=None):
    """
    Обновляет сведения о разрешенных типах ТС для перевозчиков
    """
    if vehicle_type_ids:
        vehicle_types = VehicleType.objects.filter(
            id__in=vehicle_type_ids
        ).values_list('id', flat=True)
    else:
        return

    for vehicle_type in vehicle_types:
        company.vehicle_types.add(vehicle_type)
    company.save()
    vehicle_types = set(vehicle_types)
    company_vehicle_types = set(company.vehicle_types.all())
    for vehicle_type in company_vehicle_types.difference(vehicle_types):
        company.vehicle_types.remove(vehicle_type)


def create_agent_user(company_dict, user_dict, password):
    company = Company.objects.filter(
        inn=company_dict['inn']
    ).first()
    if not company:
        company = Company.objects.create(
            name=company_dict.get('name'),
            code=company_dict.get('code'),
            inn=company_dict.get('inn'),
            status=CompanyStatus.ACTIVE,
            category=CompanyCategory.AGENT
        )
    add_ticket_types_for_agent(company, company_dict.get('ticket_types'))

    return create_user(
        company,
        user_dict,
        UserRole.AGENT,
        password
    )


def create_carrier_user(company_dict, user_dict, password):
    company = Company.objects.filter(
        inn=company_dict['inn']
    ).first()
    if not company:
        company = Company.objects.create(
            name=company_dict.get('name'),
            code=company_dict.get('code'),
            inn=company_dict.get('inn'),
            status=CompanyStatus.ACTIVE,
            category=CompanyCategory.CARRIER
        )

    add_vehicle_types_for_carrier(company, company_dict.get('vehicle_types'))
    return create_user(
        company,
        user_dict,
        UserRole.CARRIER,
        password
    )


def create_seller(company, user_dict, password):
    return create_user(
        company,
        user_dict,
        UserRole.SELLER,
        password
    )


def create_inspector(company, user_dict, password):
    return create_user(
        company,
        user_dict,
        UserRole.INSPECTOR,
        password
    )


def create_validator(company, user_dict, password):
    device_dict = None
    if 'series_number' in user_dict:
        # TODO Переделать когда будет понятно, как нужно создавать валидаторы
        device_dict = {
            'series_number': user_dict.pop('series_number'),
            'factory_number': user_dict.pop('factory_number'),
            'maker': user_dict.pop('maker'),
            'model_name': user_dict.pop('model_name')
        }
    validator = create_user(
        company,
        user_dict,
        UserRole.VALIDATOR,
        password
    )
    if device_dict:
        Device.objects.create(
            validator=validator,
            device_type=DeviceType.MAKE_TRIP,
            **device_dict
        )
    return validator


def create_workday(validator):
    return Workday.objects.create(
        validator=validator
    )


def generate_seller_token(seller):
    token = Token.objects.create(user=seller.auth_user)
    return token.key


def generate_inspector_token(inspector):
    token = Token.objects.create(user=inspector.auth_user)
    return token.key


def make_single_trip(ticket, data, validator, workday):
    vehicle_type = VehicleType.objects.get(number=data.get('vehicle_type').get('number'))
    data.pop('vehicle_type')
    trip = Operation.objects.create(
        ticket=ticket,
        created=data.pop('created', datetime.now()),
        workday=workday if workday else validator.current_workday,
        vehicle_type=vehicle_type,
        **data
    )
    return trip


def complete_ticket(ticket, data, validator, ticket_type_number=TicketType.SINGLE, workday=None):
    """
    Гашение билета
    """
    if ticket_type_number == TicketType.SINGLE:
        make_single_trip(ticket, data, validator, workday)
        ticket.set_status(TicketStatus.COMPLETED)
        return ticket


def check_completed_ticket(ticket, data):
    """
    Проверка погашенного билета
    """
    trip = ticket.operations.first()
    run_number = data.get('run_number')
    if run_number:
        if trip.run_number == run_number:
            return 'COMPLETED_HERE'
        else:
            return 'COMPLETED_NOT_HERE'
    else:
        vehicle_number = data.get('vehicle_number', trip.vehicle_number)
        carrier_code = data.get('carrier_code', trip.carrier.code)
        if 'vehicle_type' in data:
            vehicle_type = data.get('vehicle_type').get('number')
        else:
            vehicle_type = trip.vehicle_type.number
        if trip.vehicle_number == vehicle_number and \
                carrier_code == trip.carrier.code and \
                vehicle_type == trip.vehicle_type.number:
            return 'COMPLETED_HERE'
        else:
            return 'COMPLETED_NOT_HERE'


def generate_keys(
        key_path=settings.KEY_PATH,
        private_key_filename=settings.PRIVATE_KEY_FILENAME,
        public_key_filename=settings.PUBLIC_KEY_FILENAME
        ):
    key = RSA.generate(2048)
    private_key = key.export_key()
    file_out = open('/'.join([key_path, private_key_filename]), "wb")
    file_out.write(private_key)
    file_out.close()

    public_key = key.publickey().export_key()
    file_out = open('/'.join([key_path, public_key_filename]), "wb")
    file_out.write(public_key)
    file_out.close()


def create_test_tickets():
    from tickets.services.ticket_manager import SingleTicketManager
    ticket_ids = {
        'new': [],
        'complete': [],
        'disabled': [],
        'expired': [],
        'deleted': [],
        'without_signature': [],
        'wrong_signature': []
    }
    for i in range(10):
        # Создаем 10 новых билетов
        with transaction.atomic():
            tm = SingleTicketManager(
                token=get_random_string(10),
                seller=User.objects.get(name='Тестовый кассир')
            )
            ticket = Ticket.objects.create(
                token=tm.token,
                series=tm.generate_series(),
                seller_id=tm.seller.id,
                ticket_type_id=TicketType.SINGLE,
                amount=tm.get_ticket_cost(),
                start_date=tm.get_start_date(),
                end_date=tm.get_end_date()
            )
            TicketNumber.objects.create(
                ticket_id=ticket.id
            )

            qr_code = tm.generate_qr(ticket)
            ticket.qr_code = qr_code
            ticket.save()
            ticket_ids['new'].append(ticket.id)

    for i in range(3):
        # Создаем 3 погашенных билета на рейсе № 10
        with transaction.atomic():
            tm = SingleTicketManager(
                token=get_random_string(10),
                seller=User.objects.get(name='Тестовый кассир')
            )
            ticket = Ticket.objects.create(
                token=tm.token,
                series=tm.generate_series(),
                seller_id=tm.seller.id,
                ticket_type_id=TicketType.SINGLE,
                amount=tm.get_ticket_cost(),
                start_date=tm.get_start_date(),
                end_date=tm.get_end_date()
            )
            TicketNumber.objects.create(
                ticket_id=ticket.id
            )

            qr_code = tm.generate_qr(ticket)
            ticket.qr_code = qr_code
            ticket.save()

            complete_ticket(
                ticket,
                data={
                    'created': '2021-09-12 12:00',
                    'validator_number': '100',
                    'run_number': '10',
                    'vehicle_number': '123',
                    'route_number': '10',
                    'vehicle_type': {'number': 1}
                },
                validator=User.objects.get(name='Тестовый валидатор')
            )
            ticket_ids['complete'].append(ticket.id)

    for i in range(3):
        # Создаем 2 просроченных билета
        with transaction.atomic():
            tm = SingleTicketManager(
                token=get_random_string(10),
                seller=User.objects.get(name='Тестовый кассир')
            )
            ticket = Ticket.objects.create(
                token=tm.token,
                series=tm.generate_series(),
                seller_id=tm.seller.id,
                ticket_type_id=TicketType.SINGLE,
                amount=tm.get_ticket_cost(),
                start_date=datetime.now().date()-timedelta(days=31),
                end_date=datetime.now().date()-timedelta(days=11)
            )
            TicketNumber.objects.create(
                ticket_id=ticket.id
            )

            qr_code = tm.generate_qr(ticket)
            ticket.qr_code = qr_code
            ticket.save()
            ticket_ids['expired'].append(ticket.id)

    for i in range(3):
        # Создаем 2 невалидных билета
        with transaction.atomic():
            tm = SingleTicketManager(
                token=get_random_string(10),
                seller=User.objects.get(name='Тестовый кассир')
            )
            ticket = Ticket.objects.create(
                token=tm.token,
                series=tm.generate_series(),
                seller_id=tm.seller.id,
                ticket_type_id=TicketType.SINGLE,
                status=TicketStatus.DISABLED,
                amount=tm.get_ticket_cost(),
                start_date=tm.get_start_date(),
                end_date=tm.get_end_date()
            )
            TicketNumber.objects.create(
                ticket_id=ticket.id
            )

            qr_code = tm.generate_qr(ticket)
            ticket.qr_code = qr_code
            ticket.save()
            ticket_ids['disabled'].append(ticket.id)

    with transaction.atomic():
        tm = SingleTicketManager(
            token=get_random_string(10),
            seller=User.objects.get(name='Тестовый кассир')
        )
        ticket = Ticket.objects.create(
            token=tm.token,
            series=tm.generate_series(),
            seller_id=tm.seller.id,
            ticket_type_id=TicketType.SINGLE,
            status=TicketStatus.DISABLED,
            amount=tm.get_ticket_cost(),
            start_date=tm.get_start_date(),
            end_date=tm.get_end_date()
        )
        TicketNumber.objects.create(
            ticket_id=ticket.id
        )

        qr_code = tm.generate_qr(ticket)
        ticket.qr_code = qr_code
        ticket.save()
        ticket_id = ticket.id
        ticket.delete()
        ticket_ids['deleted'].append(ticket_id)

    with transaction.atomic():
        tm = SingleTicketManager(
            token=get_random_string(10),
            seller=User.objects.get(name='Тестовый кассир')
        )
        ticket = Ticket.objects.create(
            token=tm.token,
            series=tm.generate_series(),
            seller_id=tm.seller.id,
            ticket_type_id=TicketType.SINGLE,
            status=TicketStatus.DISABLED,
            amount=tm.get_ticket_cost(),
            start_date=tm.get_start_date(),
            end_date=tm.get_end_date()
        )
        TicketNumber.objects.create(
            ticket_id=ticket.id
        )

        ticket_info = {
            'ticket_id': str(ticket.id),
            'ticket_code': str(tm.ticket_type.code),
            'series': ticket.series,
            'number': str(ticket.number.id).zfill(8),
            'company_inn': tm.sm.ticket_main_company_inn,
            'agent_inn': ticket.agent_inn,
            'created_date': ticket.created.strftime('%d.%m.%Y'),
            'start_date': ticket.start_date.strftime('%d.%m.%Y'),
            'end_date': ticket.end_date.strftime('%d.%m.%Y'),
            'amount': ticket.amount,
            'algorithm': tm.algorithm
        }
        qr_code = tm.generate_test_qr(ticket, json.dumps(ticket_info))
        ticket.qr_code = qr_code
        ticket.save()
        ticket_id = ticket.id
        ticket.delete()
        ticket_ids['without_signature'].append(ticket_id)

    with transaction.atomic():
        tm = SingleTicketManager(
            token=get_random_string(10),
            seller=User.objects.get(name='Тестовый кассир')
        )
        ticket = Ticket.objects.create(
            token=tm.token,
            series=tm.generate_series(),
            seller_id=tm.seller.id,
            ticket_type_id=TicketType.SINGLE,
            status=TicketStatus.DISABLED,
            amount=tm.get_ticket_cost(),
            start_date=tm.get_start_date(),
            end_date=tm.get_end_date()
        )
        TicketNumber.objects.create(
            ticket_id=ticket.id
        )

        ticket_info = {
            'ticket_id': str(ticket.id),
            'ticket_code': str(tm.ticket_type.code),
            'series': ticket.series,
            'number': str(ticket.number.id).zfill(8),
            'company_inn': tm.sm.ticket_main_company_inn,
            'agent_inn': ticket.agent_inn,
            'created_date': ticket.created.strftime('%d.%m.%Y'),
            'start_date': ticket.start_date.strftime('%d.%m.%Y'),
            'end_date': ticket.end_date.strftime('%d.%m.%Y'),
            'amount': ticket.amount,
            'algorithm': tm.algorithm,
            'signature': get_random_string(50)
        }
        qr_code = tm.generate_test_qr(ticket, json.dumps(ticket_info))
        ticket.qr_code = qr_code
        ticket.save()
        ticket_id = ticket.id
        ticket.delete()
        ticket_ids['wrong_signature'].append(ticket_id)
    return ticket_ids







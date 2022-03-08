"""
Created on 24.08.2021

:author: Ivan Perovsky
Скрипт заполнения БД при разворачивании проекта
"""
import csv

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from django.db import transaction
from django.conf import settings as django_settings

from tickets.common.utils import get_hash_password
from tickets.models import *


INITIAL_SETTINGS = [
    {
        'name': 'agent_token_lifetime',
        'value': None,
        'description': 'Срок дейстия токена продавца. Если не указан, действует бессрочно.'
    },
    {
        'name': 'inspector_token_lifetime',
        'value': None,
        'description': 'Срок дейстия токена контроллёра. Если не указан, действует бессрочно.'
    },
    {
        'name': 'manager_token_lifetime',
        'value': None,
        'description': 'Срок дейстия токена аналитика. Если не указан, действует бессрочно.'
    },
    {
        'name': 'qr_version',
        'value': None,
        'description': 'Число от 1 до 40, контролирующее размер QR кода. 1 - 21*21. '
                       'Если не задано, нужно установить qr_fit - true',
    },
    {
        'name': 'qr_error_correction',
        'value': '0',
        'description': 'Уровень допустимых повреждений в QR коде для его читаемости. '
                       '0 - 15%, 1 - 7%, 3 - 25%, 2 - 30%'
    },
    {
        'name': 'qr_box_size',
        'value': '5',
        'description': 'Количество пикселей в квадрате QR кода'
    },
    {
        'name': 'qr_border',
        'value': '4',
        'description': 'Толщина границы QR кода'
    },
    {
        'name': 'qr_color',
        'value': 'black',
        'description': 'Цвет QR кода'
    },
    {
        'name': 'qr_back_color',
        'value': 'white',
        'description': 'Фоновый цвет QR кода'
    },
    {
        'name': 'qr_fit',
        'value': True,
        'description': 'Автоматический подбор размера'
    }
]

VEHICLE_TYPES = [
    {
        'name': 'Автобус',
        'number': 1
    },
    {
        'name': 'Трамвай',
        'number': 2
    },
    {
        'name': 'Троллейбус',
        'number': 3
    },
    {
        'name': 'Коммерческий автобус',
        'number': 4
    },
    {
        'name': 'Метрополитен',
        'number': 5
    },
    {
        'name': 'Водный транспорт',
        'number': 6
    },
]

ZONES = [
    {
        'name': 'Согласно реестру(ам) маршрутов регулярных перевозок, утвержденных распоряжением(ями) Комитета по транспорту от 31.12.2015 №212-р',
        'start_date': '2021-09-01',
        'number': 1
    }
]

TARIFFS = [
    {
        'name': 'Базовый',
        'number': 1,
        'start_date': '2021-09-01',
        'cost': '55.00'
    }
]

TICKET_TYPES = [
    {
        'name': 'Разовый проездной билет на социальный маршрут (гостевой)',
        'number': 1,
        'code': '229',
        'start_date': '2021-09-01',
        'lifetime': 30,
        'vehicle_types': (1, 2, 3)
    }
]


CARRIERS = [
    {
        'name': 'СПБ ГКУ "Организатор Перевозок"',
        'inn': '7840379186'
    },
    {
        'name': 'СПб ГУП «Пассажиравтотранс»',
        'inn': '7830001758'
    },
    {
        'name': 'СПБ ГУП "Горэлектротранс" ',
        'inn': '7830001927'
    },
    {
        'name': 'ООО "Питеравто"',
        'inn': '7819027463'
    }
]


def fill_settings_and_types():
    for setting in INITIAL_SETTINGS:
        Setting.objects.create(**setting)
    for vehicle_type in VEHICLE_TYPES:
        VehicleType.objects.create(**vehicle_type)

    for zone in ZONES:
        Zone.objects.create(**zone)
    for tariff in TARIFFS:
        Tariff.objects.create(
            name=tariff['name'],
            number=tariff['number'],
            start_date=tariff['start_date'],
            cost=tariff['cost']
        )
    for item in TICKET_TYPES:
        vehicle_types = VehicleType.objects.filter(
            number__in=item.get('vehicle_types')
        ).all()
        main_tariff = Tariff.objects.get(number=1)
        main_zone = Zone.objects.get(number=1)
        ticket_type = TicketType.objects.create(
            name=item['name'],
            number=item['number'],
            code=item['code'],
            start_date=item['start_date'],
            lifetime=item['lifetime'],
            tariff_id=main_tariff.id,
            zone_id=main_zone.id
        )
        for vehicle_type in vehicle_types:
            ticket_type.vehicle_types.add(vehicle_type)


def fill_carriers_and_routes():
    for carrier in CARRIERS:
        if carrier['inn'] == '7840379186':
            category = CompanyCategory.MAIN
        else:
            category = CompanyCategory.CARRIER
        Company.objects.create(
            category=category,
            **carrier)

    filename = 'routes.csv'
    gorelectrotrans = Company.objects.get(inn='7830001927')
    passengerautotrans = Company.objects.get(inn='7830001758')
    piterauto = Company.objects.get(inn='7819027463')
    zone = Zone.objects.filter(
        number=1
    ).first()
    with open('/'.join([settings.CSV_PATH, filename])) as csv_file:
        for row in csv.DictReader(csv_file):

            if int(row['vehicle_type']) == 1:
                company = passengerautotrans
            elif int(row['vehicle_type']) in (2, 3):
                company = gorelectrotrans
            elif int(row['vehicle_type']) == 4:
                company = piterauto

            vehicle_type = VehicleType.objects.filter(
                number=row['vehicle_type']
            ).first()
            route = Route.objects.create(
                route_number=row['route_number'],
                vehicle_type=vehicle_type,
                name=row['name']
            )
            route.carriers.add(company)
            route.save()
            zone.routes.add(route)
    zone.save()


def start_ticket_server():
    """
    Функция разворачивания проекта после применения миграций
    :return:
    """
    from tickets.common.actions import create_admin_user, generate_keys

    password = get_hash_password(django_settings.ADMIN_PASSWORD)
    create_admin_user(django_settings.ADMIN_USER, password)

    get_user_model().objects.create_superuser(
        username=django_settings.SUPERUSER_NAME,
        password=django_settings.SUPERUSER_PASSWORD
    )

    fill_settings_and_types()
    fill_carriers_and_routes()
    '''generate_keys(
        key_path=settings.KEY_PATH,
        private_key_filename=settings.PRIVATE_KEY_FILENAME,
        public_key_filename=settings.PUBLIC_KEY_FILENAME
    )'''


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with transaction.atomic():
            start_ticket_server()

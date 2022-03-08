"""
Created on 24.08.2021

:author: Ivan Perovsky
Скрипт заполнения БД при разворачивании проекта
"""
from django.core.management.base import BaseCommand

from tickets.common.utils import get_hash_password
from tickets.common.actions import create_seller, create_validator, create_inspector
from tickets.models import *


def create_users():
    """
    Функция разворачивания проекта после применения миграций
    :return:
    """
    from tickets.common.actions import create_admin_user, generate_keys

    company = Company.objects.create(
        code=123,
        name='Тестовый агент',
        inn='780000000',
        status=CompanyStatus.ACTIVE,
        category=CompanyCategory.AGENT
    )
    seller_password = '2UGkArD4'
    seller_login = 'seller@mybstr.com'
    password = get_hash_password(seller_password)
    print(password)

    seller = create_seller(
        company=company,
        user_dict={
            'login': seller_login,
            'name': 'Тестовый кассир',
            'code': 111
        },
        password=password
    )

    carrier = Company.objects.get(inn='7830001758')
    validator_password = 's32hUKZL'
    validator_login = 'validator@mybstr.com'
    password = get_hash_password(validator_password)
    print(password)

    validator = create_validator(
        company=carrier,
        user_dict={
            'login': validator_login,
            'name': 'Тестовый валидатор',
            'code': 222
        },
        password=password
    )

    inspector_password = '6Rg7eUlB'
    inspector_login = 'inspector@mybstr.com'
    password = get_hash_password(inspector_password)
    print(password)

    inspector = create_inspector(
        company=carrier,
        user_dict={
            'login': inspector_login,
            'name': 'Тестовый контроллер',
            'code': 333
        },
        password=password
    )


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with transaction.atomic():
            create_users()

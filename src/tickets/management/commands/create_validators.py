from django.core.management.base import BaseCommand

from tickets.common.utils import get_hash_password
from tickets.common.actions import create_validator
from tickets.models import *
VALIDATORS = [
    {
        'login': 'one@mybstr.com',
        'password': '5NTkHlnE',
        'name': 'validator 1',
        'code': 1111
    },
    {
        'login': 'two@mybstr.com',
        'password': 'saEl8TsQ',
        'name': 'validator 2',
        'code': 2222
    },
    {
        'login': 'three@mybstr.com',
        'password': 'pH1yxwaD',
        'name': 'validator 3',
        'code': 3333
    },
    {
        'login': 'four@mybstr.com',
        'password': 'mPLBNwlc',
        'name': 'validator 4',
        'code': 4444
    },
    {
        'login': 'five@mybstr.com',
        'password': 'LlLE7Npf',
        'name': 'validator 5',
        'code': 5555
    },
    {
        'login': 'six@mybstr.com',
        'password': 'RTs3sfxX',
        'name': 'validator 6',
        'code': 6666
    },
    {
        'login': 'seven@mybstr.com',
        'password': 'IXXgLExy',
        'name': 'validator 7',
        'code': 7777
    },
    {
        'login': 'eight@mybstr.com',
        'password': 'pao4bh3x',
        'name': 'validator 8',
        'code': 8888
    }
]


def create_validators():
    """
    Функция создания массива валидаторов
    :return:
    """
    carrier = Company.objects.get(inn='7830001758')
    for item in VALIDATORS:
        create_validator(
            company=carrier,
            user_dict={
                'login': item['login'],
                'name': item['name'],
                'code': item['code']
            },
            password=get_hash_password(item['password'])
        )


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with transaction.atomic():
            create_validators()

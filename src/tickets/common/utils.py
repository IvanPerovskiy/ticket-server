"""
Created on 24.08.2021

:author: Ivan Perovsky
Вспомогательные функции
"""

import pytz
import base64
import hashlib

from datetime import datetime, timedelta, date

from django.conf import settings


def b64e(s):
    return base64.b64encode(s.encode('utf-8')).decode('utf-8')


def b64d(s):
    return base64.b64decode(s).decode('utf-8')


def empty_to_none(item, attribute):
    """
    Возвращает значение атрибута объекта,
    если объект и атрибут существуют и имеют непустое значение
    """
    if item and hasattr(item, attribute):
        return getattr(item, attribute, None)


def empty_attr_to_none(item, attrs):
    for attr in attrs:
        if not item:
            return ''
        item = getattr(item, attr, '')

    return item


def get_first_value(values):
    """
    Возвращает первое ненулевое значение из списка
    """
    for value in values:
        if value:
            return value


def get_hash_password(password):
    h = hashlib.sha256()
    h.update(password.encode('utf-8'))
    return h.hexdigest()


def check_request_params(arr, params):
    """
    Проверяет присутствие всех параметров params в списке arr
    """
    return all(arr.get(elem) for elem in params)


def get_local_current_date():
    """
    Возвращает текущую дату по часовому поясу Камбарки
    """
    current_timezone = pytz.timezone(settings.CELERY_TIMEZONE)
    return datetime.now(current_timezone).date()


def get_local_interval(start_date, end_date):
    start_date = datetime.strptime(start_date, ('%Y-%m-%d'))
    end_date = datetime.strptime(end_date, ('%Y-%m-%d'))
    start_date = start_date - timedelta(hours=settings.UTC_DELTA)
    end_date = end_date - timedelta(hours=settings.UTC_DELTA, microseconds=1)
    return start_date.strftime('%Y-%m-%d %H:%M:%S.%f'), end_date.strftime('%Y-%m-%d %H:%M:%S.%f')


def get_local_datetime(input_dt):
    """
    Возвращает строку локального времени определенного формата
    :param datetime input_dt: время UTC
    :rtype: str
    :return: локальное время
    """
    current_timezone = pytz.timezone(settings.CELERY_TIMEZONE)
    input_dt = input_dt.replace(tzinfo=None)
    return pytz.utc.localize(input_dt).astimezone(current_timezone).strftime(
        settings.REST_FRAMEWORK.get('DATETIME_FORMAT')
    )


def get_local_current_date_string(format='%Y.%m.%d'):
    """
    Возвращает текущую дату по часовому поясу Камбарки
    """
    current_timezone = pytz.timezone(settings.CELERY_TIMEZONE)
    return datetime.now(current_timezone).strftime(format)


def get_date_string(input_dt, format='%d.%m.%Y'):
    """
    Возвращает дату в виде строки в определенном формате
    """
    if isinstance(input_dt, date) or isinstance(input_dt, datetime):
        return input_dt.strftime(format)
    elif isinstance(input_dt, str):
        return datetime.strptime(input_dt, '%Y-%m-%d').strftime(format)


def get_local_current_datetime_string():
    """
    Возвращает текущую дату по часовому поясу Камбарки
    """
    current_timezone = pytz.timezone(settings.CELERY_TIMEZONE)
    return datetime.now(current_timezone).strftime('%Y-%m-%d_%H%M%S')


def get_local_tomorrow_date():
    """
    Возвращает завтрашнюю дату по часовому поясу Камбарки
    """
    current_timezone = pytz.timezone(settings.CELERY_TIMEZONE)
    return (datetime.now(current_timezone) + timedelta(days=1)).date()


def timezone_converter(input_dt, target_tz=settings.CELERY_TIMEZONE):
    target_tz = pytz.timezone(target_tz)
    target_dt = input_dt.astimezone(target_tz)
    return target_tz.normalize(target_dt)


def parse_datetime(input_dt):
    str_dt = input_dt.strftime("%Y-%m-%dT%H:%M:%S")
    return (str_dt[:10], str_dt[11:])


def format_datetime(input_dt):
    return input_dt.strftime("%Y-%m-%d %H:%M:%S")


def get_reporing_period():
    # Возвращает даты интервала прошлого месяца
    first_day_of_current_month = date.today().replace(day=1)
    last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_previous_month = last_day_of_previous_month.replace(day=1)
    return first_day_of_current_month.strftime('%Y-%m-%d'), first_day_of_previous_month.strftime('%Y-%m-%d')


class LicensePlate:
    choices = {'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H',
               'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T', 'У': 'Y', 'Х': 'X'}

    @classmethod
    def converter_latin(self, simbols):
        return ''.join([self.choices.get(i) or i for i in simbols])

    @classmethod
    def converter_cyrillic(self, simbols):
        choices = dict(zip(self.choices.values(), self.choices.keys()))
        return ''.join([choices.get(i) or i for i in simbols])

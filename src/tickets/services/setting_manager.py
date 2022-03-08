"""
Created on 26.08.2021

:author: Ivan Perovsky
Сервис для извлечения настроек из БД
"""
from tickets.models import Setting, Company


class MetaSettingManager(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(MetaSettingManager, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SettingManager(metaclass=MetaSettingManager):
    """
    Синглтон для работы с настройками
    При инициализации извлекает только общие настройки и настройки QR кода.
    """
    def __init__(self):
        self.select_general_settings()
        self.select_main_company_settings()

    def select_general_settings(self):
        settings = Setting.objects.values('name', 'value')
        for setting in settings:
            value = Setting.objects.filter(name=setting['name']).first().value
            setattr(self, setting['name'], value)

    def select_main_company_settings(self):
        main_company = Company.objects.filter(inn='7840379186').first()
        self.ticket_main_company_inn = main_company.inn
        self.ticket_main_company = main_company.name

    def refresh_from_db(self, is_company_changed=False):
        """
        Обновляет общие настройки после изменения в бд
        """
        self.select_general_settings()
        if is_company_changed:
            self.select_main_company_settings()

    def clear(self):
        """
        Удаляет все атрибуты
        """

        settings = Setting.objects.values('name')
        attrs = [setting['name'] for setting in settings]
        for attr in attrs:
            delattr(self, attr)








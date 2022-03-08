"""
Created on 24.08.2021

:author: Ivan Perovsky
Декораторы
"""
from functools import wraps

from rest_framework import status
from rest_framework.response import Response

from tickets.models import UserRole


def roles_required(roles):
    """
    Позволяет вызывать метод пользователсям только с
    определенными ролями
    :param tuple roles: роли пользователей
    """
    def decorator(f):
        @wraps(f)
        def wrapper(self, request, **kwargs):
            role = request.user.user.role
            if role is None or role not in roles:
                return Response(status=status.HTTP_403_FORBIDDEN)
            return f(self, request, **kwargs)
        return wrapper
    return decorator


def admin_required(f):
    return roles_required(
        (UserRole.ADMIN,)
    )(f)


def security_admin_required(f):
    return roles_required(
        (UserRole.ADMIN, UserRole.SECURITY_ADMIN)
    )(f)


def carrier_required(f):
    return roles_required(
        (UserRole.ADMIN, UserRole.CARRIER, UserRole.SECURITY_ADMIN)
    )(f)


def agent_carrier_required(f):
    return roles_required(
        (UserRole.AGENT, UserRole.ADMIN, UserRole.CARRIER, UserRole.SECURITY_ADMIN)
    )(f)


def agent_required(f):
    return roles_required(
        (UserRole.ADMIN, UserRole.AGENT, UserRole.SECURITY_ADMIN)
    )(f)


def seller_agent_required(f):
    return roles_required(
        (UserRole.SELLER, UserRole.ADMIN, UserRole.AGENT, UserRole.SECURITY_ADMIN)
    )(f)


def seller_required(f):
    return roles_required(
        (UserRole.SELLER,)
    )(f)


def inspector_required(f):
    return roles_required(
        (UserRole.INSPECTOR,)
    )(f)


def validator_required(f):
    return roles_required(
        (UserRole.VALIDATOR,)
    )(f)


def read_only_admin_model(*non_display_fields):
    """
        Декоратор для класса отображения модели в админке, который делает модель доступной только для чтения
        В качестве аргумента принимает список полей, которые нужно скрыть в самой модели
        По умолчанию запрещает создавать и удалять объекты модели
    """

    class ClassWrapper:
        def __init__(self, cls):
            self.other_class = cls
            self.other_class.has_add_permission = lambda self, request: False
            self.other_class.has_delete_permission = lambda self, request, obj=None: False

            if non_display_fields:

                def get_fields(self, request, obj=None):
                    fields = super(cls, self).get_fields(request, obj)
                    for field in non_display_fields:
                        fields.remove(field)
                    return fields

                self.other_class.get_fields = get_fields

        def __call__(self, *cls_ars):
            other = self.other_class(*cls_ars)
            return other

    return ClassWrapper

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, ListModelMixin
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from tickets.serializers import *
from tickets.common.decorators import admin_required
from tickets.services.setting_manager import SettingManager
from tickets.common.responses import NOT_FOUND, BAD_REQUEST, ACCESS_FORBIDDEN, SUCCESS_RESPONSE


class SettingViewSet(
    viewsets.GenericViewSet
):
    queryset = Setting.objects.all()
    serializer_class = SettingSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['name']
    ordering_fields = ['id']

    setting_response = openapi.Response(SUCCESS_RESPONSE, SettingSerializer)

    def get_serializer_class(self):
        if self.action == 'create':
            return SettingCreateSerializer
        if self.action == 'update':
            return SettingUpdateSerializer
        return self.serializer_class

    @admin_required
    def retrieve(self, request, *args, **kwargs):
        """
        Доступно только администратору
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @admin_required
    def list(self, request, *args, **kwargs):
        """
        Доступно только администратору
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(responses={
        200: setting_response,
        400: BAD_REQUEST,
        403: ACCESS_FORBIDDEN,
        404: NOT_FOUND
    })
    @admin_required
    def update(self, request, *args, **kwargs):
        """
        Обновляет значение параметра настройки.
        Доступно только администратору
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Перезагружаем менеджер настроек после изменений
        sm = SettingManager()
        sm.refresh_from_db()
        return Response(SettingSerializer(instance=instance).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={
        201: setting_response,
        400: BAD_REQUEST,
        403: ACCESS_FORBIDDEN,
        404: NOT_FOUND
    })
    @admin_required
    def create(self, request, *args, **kwargs):
        """
        Доступно только администратору
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Перезагружаем менеджер настроек после изменений
        sm = SettingManager()
        sm.refresh_from_db()
        return Response(serializer.data, status=status.HTTP_201_CREATED)




import io
import csv

from django.utils.crypto import get_random_string
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from tickets.serializers import *
from tickets.common.decorators import admin_required, agent_required
from tickets.common.actions import create_seller, generate_seller_token, create_agent_user
from tickets.common.utils import get_hash_password
from tickets.common.responses import IMPOSSIBLE_UPDATE_STATUS, SUCCESS_CREATE, \
    NOT_FOUND, BAD_REQUEST, ACCESS_FORBIDDEN, SUCCESS_CREATE_AGENT, SUCCESS_RESPONSE, COMPANY_ID_NOT_FOUND


class AgentViewSet(viewsets.GenericViewSet):
    queryset = Company.objects.filter(
        category=CompanyCategory.AGENT
    ).prefetch_related('users')
    serializer_class = AgentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['name', 'status', 'inn']
    ordering_fields = ['name']
    ordering = ['name']

    create_agent_response = openapi.Response(SUCCESS_CREATE_AGENT, UserSerializerResponse)
    update_agent_response = openapi.Response(SUCCESS_RESPONSE, AgentSerializer)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserAgentCreateSerializer
        if self.action == 'update':
            return AgentUpdateSerializer
        return self.serializer_class

    @swagger_auto_schema(responses={
        201: create_agent_response,
        400: BAD_REQUEST,
        403: ACCESS_FORBIDDEN
    })
    @admin_required
    def create(self, request, *args, **kwargs):
        """
        Создает компанию и пользователя с ролью Агент.
        Если компания существует, просто создает ее пользователя.
        В случае передачи пароля сохраняет его, если не передан, генерирует на своей стороне и возвращает.
        Доступно только администратору
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['user'].get('password')
        new_password = None
        if not password:
            new_password = get_random_string()
            password = get_hash_password(new_password)
        else:
            password = get_hash_password(password)
        user = create_agent_user(
            company_dict=serializer.validated_data['company'],
            user_dict=serializer.validated_data['user'],
            password=password
        )
        data = {
            'user_id': user.id,
            'company_id': user.company.id,
            'login': user.login
        }
        if new_password:
            data['password'] = new_password
        return Response(data=data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(responses={
        200: update_agent_response,
        400: BAD_REQUEST,
        403: ACCESS_FORBIDDEN,
        404: NOT_FOUND
    })
    @admin_required
    def update(self, request, *args, **kwargs):
        """
        Обновляет данные компании.
        Доступно только администратору
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

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

    @admin_required
    def retrieve(self, request, *args, **kwargs):
        """
        Доступно только администратору
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={
        200: update_agent_response,
        400: IMPOSSIBLE_UPDATE_STATUS,
        404: NOT_FOUND
    })
    @admin_required
    @action(
        detail=True,
        url_path='update-status',
        methods=['put'],
        serializer_class=SerializerUpdateStatus
    )
    def update_status(self, request, *args, **kwargs):
        """
        Доступно только администратору
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(AgentSerializer(instance).data, status=status.HTTP_200_OK)


class SellerViewSet(viewsets.GenericViewSet):
    queryset = User.objects.filter(
        role=UserRole.SELLER
    ).select_related('company')
    serializer_class = UserSerializerItem
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['name', 'status', 'inn']
    ordering_fields = ['name']
    ordering = ['name']

    create_seller_response = openapi.Response(SUCCESS_RESPONSE, UserSerializerResponse)
    create_sellers_response = openapi.Response(SUCCESS_RESPONSE, UsersSerializerResponse)
    update_seller_response = openapi.Response(SUCCESS_RESPONSE, UserSerializerItem)

    def get_queryset(self):
        if self.request.user.user.role == UserRole.AGENT:
            return User.objects.filter(
                role=UserRole.SELLER,
                company=self.request.user.user.company
            ).select_related('company')
        elif self.request.user.user.role in (UserRole.ADMIN, UserRole.SECURITY_ADMIN):
            return User.objects.filter(
                role=UserRole.SELLER,
            ).select_related('company')

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return self.serializer_class

    @agent_required
    def list(self, request, *args, **kwargs):
        """
        Доступно ролям АДМИН и АГЕНТ (только свои точки продажи)
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @agent_required
    def retrieve(self, request, *args, **kwargs):
        """
        Доступно ролям АДМИН и АГЕНТ (только свои точки продажи)
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={
        201: create_seller_response,
        400: BAD_REQUEST,
        403: ACCESS_FORBIDDEN
    })
    @agent_required
    def create(self, request, *args, **kwargs):
        """
        Доступно ролям АДМИН и АГЕНТ
        """
        password = self.request.data.get('password')
        current_user = self.request.user.user
        if current_user.role in (UserRole.ADMIN, UserRole.SECURITY_ADMIN):
            company_id = self.request.data.get('company_id')
            if not company_id:
                return Response(
                    COMPANY_ID_NOT_FOUND,
                    status=status.HTTP_400_BAD_REQUEST
                )
            company = Company.objects.filter(id=company_id).first()
            if not company:
                return Response(
                    NOT_FOUND,
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            company = self.request.user.user.company

        new_password = None
        if not password:
            new_password = get_random_string()
            password = get_hash_password(new_password)
        else:
            password = get_hash_password(password)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = create_seller(
            company=company,
            user_dict=serializer.validated_data,
            password=password
        )
        data = {
            'user_id': user.id,
            'login': user.login
        }
        if new_password:
            data['password'] = new_password
        return Response(data=data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(responses={
        201: create_sellers_response,
        400: BAD_REQUEST,
        403: ACCESS_FORBIDDEN
    })
    @agent_required
    @action(
        detail=False,
        methods=['post'],
        url_path='csv',
        serializer_class=UsersCreateSerializer
    )
    def create_from_csv(self, request, *args, **kwargs):
        """
        Создание точек продажи из csv файла.
        Поля файла ['seller_name', 'seller_code', 'address']
        Доступно ролям АДМИН и АГЕНТ
        """
        current_user = self.request.user.user
        if current_user.role in (UserRole.ADMIN, UserRole.SECURITY_ADMIN):
            company_id = request.data.get('company_id')
            if not company_id:
                return Response(
                    COMPANY_ID_NOT_FOUND,
                    status=status.HTTP_400_BAD_REQUEST
                )
            company = Company.objects.filter(id=company_id).first()
            if not company:
                return Response(
                    NOT_FOUND,
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            company = self.request.user.user.company
        if file_csv := request.data.get('file'):
            message = base64.b64decode(file_csv).decode('utf-8')
            count_error_items = 0
            count_double_items = 0
            count_created_items = 0
            result_data = []
            required_fieldnames = ['seller_name', 'seller_code', 'address']
            with io.StringIO(message) as fp:
                reader = csv.DictReader(fp, delimiter=",", quotechar='"')
                if reader.fieldnames != required_fieldnames:
                    return Response(
                        'Поля файла не соответствуют шаблону',
                        status=status.HTTP_400_BAD_REQUEST
                    )
                for row in reader:
                    try:
                        with transaction.atomic():
                            seller = User.objects.filter(
                                code=row['seller_code'],
                                company_id=company.id
                            ).first()
                            if not seller:
                                user_dict = {
                                    'name': row['seller_name'],
                                    'code': row['seller_code'],
                                    'address': row['address']
                                }
                                new_password = get_random_string()
                                password = get_hash_password(new_password)
                                user = create_seller(company, user_dict, password)
                                count_created_items += 1
                                seller_data = {
                                    'user_id': user.id,
                                    'login': user.login,
                                    'address': user.address,
                                    'password': new_password
                                }
                                result_data.append(seller_data)
                            else:
                                count_double_items += 1
                    except:
                        count_error_items += 1

            with open('/'.join([settings.CSV_PATH, 'seller_login.csv']), 'w', newline='', encoding='utf-8') as content:
                fieldnames = ('user_id', 'address', 'login', 'password')
                writer = csv.DictWriter(content, fieldnames=fieldnames)
                writer.writeheader()

                for row in result_data:
                    writer.writerow(row)

            with open('/'.join([settings.CSV_PATH, 'seller_login.csv']), 'r', encoding='utf-8') as content:
                body = base64.b64encode(content.read().encode("UTF-8"))

            # os.remove('/'.join([settings.CSV_PATH, 'sellers.csv'])) TODO добавить после всех тестирований

            data = {
                'count_error_items': count_error_items,
                'count_double_items': count_double_items,
                'count_created_items': count_created_items,
                'file': body
            }
            http_status = status.HTTP_200_OK
            if count_created_items > 0:
                http_status = status.HTTP_201_CREATED
            return Response(data, status=http_status)

        return Response('Файл не распознан', status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses={
        200: update_seller_response,
        400: IMPOSSIBLE_UPDATE_STATUS,
        404: NOT_FOUND
    })
    @admin_required
    @action(
        detail=True,
        url_path='update-status',
        methods=['put'],
        serializer_class=SerializerUpdateStatus
    )
    def update_status(self, request, *args, **kwargs):
        """
        Доступно ролям АДМИН и АГЕНТ
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(UserSerializerItem(instance).data, status=status.HTTP_200_OK)


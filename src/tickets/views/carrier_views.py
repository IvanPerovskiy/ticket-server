import io
import csv

from django.utils.crypto import get_random_string
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from tickets.serializers import *
from tickets.common.decorators import admin_required, carrier_required, validator_required
from tickets.common.actions import create_inspector, create_carrier_user, create_validator, \
    create_workday, complete_ticket
from tickets.common.utils import get_hash_password
from tickets.common.responses import IMPOSSIBLE_UPDATE_STATUS, COMPANY_ID_NOT_FOUND, \
    NOT_FOUND, BAD_REQUEST, ACCESS_FORBIDDEN, SUCCESS_CREATE_CARRIER, SUCCESS_RESPONSE, WORKDAY_ALREADY_OPEN,\
    WORKDAY_NOT_FOUND, WORKDAY_ALREADY_CLOSED


class CarrierViewSet(viewsets.GenericViewSet):
    queryset = Company.objects.filter(
        category=CompanyCategory.CARRIER
    ).prefetch_related('users')
    serializer_class = CarrierSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['name', 'status', 'inn']
    ordering_fields = ['name']
    ordering = ['name']

    create_carrier_response = openapi.Response(SUCCESS_CREATE_CARRIER, UserSerializerResponse)
    update_carrier_response = openapi.Response(SUCCESS_RESPONSE, CarrierSerializer)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCarrierCreateSerializer
        if self.action == 'update':
            return CarrierUpdateSerializer
        return self.serializer_class

    @swagger_auto_schema(responses={
        200: update_carrier_response,
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
        201: create_carrier_response,
        400: BAD_REQUEST,
        403: ACCESS_FORBIDDEN
    })
    @admin_required
    def create(self, request, *args, **kwargs):
        """
        Создает компанию и пользователя с ролью Перевозчик.
        Если компания существует, просто создает ее пользователя
        В случае передачи пароля сохраняет его, если не передан, генерирует на своей стороне и возвращает
        Доступно только администратору
        """
        password = self.request.data.get('password')
        new_password = None
        if not password:
            new_password = get_random_string()
            password = get_hash_password(new_password)
        else:
            password = get_hash_password(password)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = create_carrier_user(
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
        200: update_carrier_response,
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
        Изменение статуса Перевозчика
        Доступно только администратору
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(CarrierSerializer(instance).data, status=status.HTTP_200_OK)


class InspectorViewSet(viewsets.GenericViewSet):
    queryset = User.objects.filter(
        role=UserRole.INSPECTOR
    ).select_related('company')
    serializer_class = UserSerializerItem
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['name', 'status', 'inn']
    ordering_fields = ['name']
    ordering = ['name']

    create_inspector_response = openapi.Response(SUCCESS_RESPONSE, UserSerializerResponse)
    create_inspectors_response = openapi.Response(SUCCESS_RESPONSE, UsersSerializerResponse)
    update_inspectors_response = openapi.Response(SUCCESS_RESPONSE, UserSerializerItem)

    def get_queryset(self):
        if self.request.user.user.role == UserRole.CARRIER:
            return User.objects.filter(
                role=UserRole.INSPECTOR,
                company=self.request.user.user.company
            ).select_related('company')
        elif self.request.user.user.role in (UserRole.ADMIN, UserRole.SECURITY_ADMIN):
            return User.objects.filter(
                role=UserRole.INSPECTOR,
            ).select_related('company')

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return self.serializer_class

    def list(self, request, *args, **kwargs):
        """
        Доступно ролям АДМИН и ПЕРЕВОЗЧИК (только свои контроллёры)
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        Доступно ролям АДМИН и ПЕРЕВОЗЧИК (только свои контроллёры)
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={
        201: create_inspector_response,
        400: BAD_REQUEST,
        403: ACCESS_FORBIDDEN
    })
    @carrier_required
    def create(self, request, *args, **kwargs):
        """
        Доступно ролям АДМИН и ПЕРЕВОЗЧИК
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
        user = create_inspector(
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
        201: create_inspectors_response,
        400: BAD_REQUEST,
        403: ACCESS_FORBIDDEN
    })
    @carrier_required
    @action(
        detail=False,
        methods=['post'],
        url_path='csv',
        serializer_class=UsersCreateSerializer
    )
    def create_from_csv(self, request, *args, **kwargs):
        """
        Создание контроллёров из csv файла.
        Поля файла ['inspector_name', 'inspector_code', 'position']
        Доступно ролям АДМИН и ПЕРЕВОЗЧИК
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
            required_fieldnames = ['inspector_name', 'inspector_code', 'position']
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
                            inspector = User.objects.filter(
                                code=row['inspector_code'],
                                company_id=company.id
                            ).first()
                            if not inspector:
                                user_dict = {
                                    'name': row['inspector_name'],
                                    'code': row['inspector_code'],
                                    'position': row['position']
                                }
                                new_password = get_random_string()
                                password = get_hash_password(new_password)
                                user = create_inspector(company, user_dict, password)
                                count_created_items += 1
                                inspector_data = {
                                    'user_id': user.id,
                                    'name': user.name,
                                    'login': user.login,
                                    'password': new_password
                                }
                                result_data.append(inspector_data)
                            else:
                                count_double_items += 1
                    except:
                        count_error_items += 1

            with open('/'.join([settings.CSV_PATH, 'inspector_login.csv']), 'w', newline='', encoding='utf-8') as content:
                fieldnames = ('user_id', 'name', 'login', 'password')
                writer = csv.DictWriter(content, fieldnames=fieldnames)
                writer.writeheader()

                for row in result_data:
                    writer.writerow(row)

            with open('/'.join([settings.CSV_PATH, 'inspector_login.csv']), 'r', encoding='utf-8') as content:
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
        200: update_inspectors_response,
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
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(UserSerializerItem(instance).data, status=status.HTTP_200_OK)


class ValidatorViewSet(viewsets.GenericViewSet):
    queryset = User.objects.filter(
        role=UserRole.VALIDATOR
    ).select_related('company')
    serializer_class = UserSerializerItem
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['name', 'status', 'inn']
    ordering_fields = ['name']
    ordering = ['name']

    create_validator_response = openapi.Response(SUCCESS_RESPONSE, UserSerializerResponse)
    create_validators_response = openapi.Response(SUCCESS_RESPONSE, UsersSerializerResponse)
    update_validators_response = openapi.Response(SUCCESS_RESPONSE, UserSerializerItem)

    def get_queryset(self):
        if self.request.user.user.role == UserRole.CARRIER:
            return User.objects.filter(
                role=UserRole.VALIDATOR,
                company=self.request.user.user.company
            ).select_related('company')
        elif self.request.user.user.role in (UserRole.ADMIN, UserRole.SECURITY_ADMIN):
            return User.objects.filter(
                role=UserRole.VALIDATOR,
            ).select_related('company')

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return self.serializer_class

    def list(self, request, *args, **kwargs):
        """
        Доступно ролям АДМИН и ПЕРЕВОЗЧИК (только свои валидаторы)
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        Доступно ролям АДМИН и ПЕРЕВОЗЧИК (только свои валидаторы)
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={
        201: create_validator_response,
        400: BAD_REQUEST,
        403: ACCESS_FORBIDDEN
    })
    @carrier_required
    def create(self, request, *args, **kwargs):
        """
        Доступно ролям АДМИН и ПЕРЕВОЗЧИК
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
        user = create_validator(
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
        201: create_validators_response,
        400: BAD_REQUEST,
        403: ACCESS_FORBIDDEN
    })
    @carrier_required
    @action(
        detail=False,
        methods=['post'],
        url_path='csv',
        serializer_class=UsersCreateSerializer
    )
    def create_from_csv(self, request, *args, **kwargs):
        """
        Создание валидаторов из csv файла.
        Поля файла ['name', 'code', 'series_number', 'factory_number', 'maker', 'model_name']
        Доступно ролям АДМИН и ПЕРЕВОЗЧИК
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
            required_fieldnames = ['name', 'code', 'series_number', 'factory_number', 'maker', 'model_name']
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
                            validator = User.objects.filter(
                                code=row['code'],
                                company_id=company.id
                            ).first()
                            if not validator:
                                user_dict = {
                                    'name': row['name'],
                                    'code': row['code'],
                                    'series_number': row['series_number'],
                                    'factory_number': row['factory_number'],
                                    'maker': row['maker'],
                                    'model_name': row['model_name']
                                }
                                new_password = get_random_string()
                                password = get_hash_password(new_password)
                                user = create_validator(company, user_dict, password)
                                count_created_items += 1
                                inspector_data = {
                                    'user_id': user.id,
                                    'name': user.name,
                                    'login': user.login,
                                    'password': new_password
                                }
                                result_data.append(inspector_data)
                            else:
                                count_double_items += 1
                    except:
                        count_error_items += 1

            with open('/'.join([settings.CSV_PATH, 'validator_login.csv']), 'w', newline='', encoding='utf-8') as content:
                fieldnames = ('user_id', 'name', 'login', 'password')
                writer = csv.DictWriter(content, fieldnames=fieldnames)
                writer.writeheader()

                for row in result_data:
                    writer.writerow(row)

            with open('/'.join([settings.CSV_PATH, 'validator_login.csv']), 'r', encoding='utf-8') as content:
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
        200: update_validators_response,
        400: IMPOSSIBLE_UPDATE_STATUS,
        404: NOT_FOUND
    })
    @carrier_required
    @action(
        detail=True,
        url_path='update-status',
        methods=['put'],
        serializer_class=SerializerUpdateStatus
    )
    def update_status(self, request, *args, **kwargs):
        """
        Доступно ролям АДМИН и ПЕРЕВОЗЧИК
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(UserSerializerItem(instance).data, status=status.HTTP_200_OK)


class WorkdayViewSet(viewsets.GenericViewSet):
    queryset = Workday.objects.select_related('validator')

    open_workday_response = openapi.Response(SUCCESS_RESPONSE, WorkdayOpenSerializer)
    close_workday_response = openapi.Response(SUCCESS_RESPONSE, WorkdayCloseSerializer)

    @swagger_auto_schema(responses={
        200: open_workday_response,
        400: WORKDAY_ALREADY_OPEN
    })
    @validator_required
    @action(
        detail=False,
        methods=['post'],
        url_path='open'
    )
    def create_workday(self, request, **kwargs):
        """
        Открытие смены
        """
        validator = self.request.user.user
        if validator.current_workday:
            return Response(WORKDAY_ALREADY_OPEN, status=status.HTTP_400_BAD_REQUEST)
        workday = create_workday(validator)
        pub_key = open('/'.join([
            settings.KEY_PATH,
            settings.PUBLIC_KEY_FILENAME
        ])).read()
        data = {
            'workday_id': workday.id,
            'pub_key': pub_key
        }
        return Response(data=data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={
        200: SUCCESS_RESPONSE,
        400: WORKDAY_NOT_FOUND,
        403: ACCESS_FORBIDDEN,
        404: WORKDAY_NOT_FOUND
    })
    @validator_required
    @action(
        detail=True,
        methods=['post'],
        url_path='close',
        serializer_class=LoadTripsSerializer
    )
    def close_workday(self, request, **kwargs):
        """
        Закрытие смены
        """
        validator = self.request.user.user
        workday = self.get_object()

        if not workday:
            return Response(WORKDAY_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        if workday.validator.id != validator.id:
            return Response(ACCESS_FORBIDDEN, status=status.HTTP_403_FORBIDDEN)
        if workday.status != WorkdayStatus.OPEN:
            return Response(WORKDAY_ALREADY_CLOSED, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for item in serializer.validated_data['tickets']:
            ticket = Ticket.objects.filter(
                id=item.get('ticket').get('id')
            ).first()
            item.pop('ticket')
            if ticket and ticket.status == TicketStatus.ACTIVE:
                complete_ticket(ticket, item, self.request.user.user, workday=workday)

        workday.status = WorkdayStatus.CLOSED
        workday.closed = datetime.now()
        workday.save()
        return Response(status=status.HTTP_200_OK)

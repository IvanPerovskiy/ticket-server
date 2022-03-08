from django.contrib.auth import authenticate
from django.utils.crypto import get_random_string
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from tickets.serializers import *
from tickets.common.utils import get_hash_password
from tickets.common.decorators import admin_required, seller_agent_required, agent_carrier_required
from tickets.common.responses import TARIFF_NOT_FOUND, SUCCESS_UPDATE_TARIFF, \
    IMPOSSIBLE_UPDATE_TARIFF, SUCCESS_UPDATE_TICKETTYPE, TICKET_TYPE_NOT_FOUND, IMPOSSIBLE_UPDATE_STATUS, \
    NOT_FOUND, BAD_REQUEST, ACCESS_FORBIDDEN, SUCCESS_RESPONSE


class TariffViewSet(viewsets.GenericViewSet):
    queryset = Tariff.objects.all()
    serializer_class = TariffSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['name', 'status']
    ordering_fields = ['created', 'name']
    ordering = ['-created']

    update_tariff_response = openapi.Response(SUCCESS_UPDATE_TARIFF, TariffSerializer)

    def get_serializer_class(self):
        if self.action == 'update':
            return TariffSerializerUpdate
        return self.serializer_class

    @admin_required
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @admin_required
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @admin_required
    def create(self, request, *args, **kwargs):
        """
        Доступно только администратору
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(responses={
        200: update_tariff_response,
        400: IMPOSSIBLE_UPDATE_TARIFF,
        404: TARIFF_NOT_FOUND
    })
    @admin_required
    def update(self, request, *args, **kwargs):
        """
        Доступно только администратору
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(tariff_id=instance.id)

        return Response(TariffSerializer(instance).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={
        200: update_tariff_response,
        400: IMPOSSIBLE_UPDATE_STATUS,
        404: TARIFF_NOT_FOUND
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

        return Response(TicketTypeSerializer(instance).data, status=status.HTTP_200_OK)


class TicketTypeViewSet(viewsets.GenericViewSet):
    queryset = TicketType.objects.all()
    serializer_class = TicketTypeSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['name', 'status']
    ordering_fields = ['created', 'name']
    ordering = ['-created']

    update_ticket_type_response = openapi.Response(SUCCESS_UPDATE_TICKETTYPE, TicketTypeSerializer)

    def get_serializer_class(self):
        if self.action == 'update':
            return TicketTypeSerializerUpdate
        return self.serializer_class

    def get_queryset(self):
        if self.request.user.user.role in (UserRole.AGENT, UserRole.SELLER):
            company = self.request.user.user.company
            return company.ticket_types.all()
        elif self.request.user.user.role in (UserRole.ADMIN, UserRole.SECURITY_ADMIN):
            return self.queryset

    @seller_agent_required
    def retrieve(self, request, *args, **kwargs):
        """
        Доступно пользователям с ролью АДМИН, КАССИР, АГЕНТ
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @seller_agent_required
    def list(self, request, *args, **kwargs):
        """
        Доступно пользователям с ролью АДМИН, КАССИР, АГЕНТ
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @admin_required
    def create(self, request, *args, **kwargs):
        """
        Доступно только администратору
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(responses={
        200: update_ticket_type_response,
        404: TICKET_TYPE_NOT_FOUND
    })
    @admin_required
    def update(self, request, *args, **kwargs):
        """
        Доступно только администратору
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(TicketTypeSerializer(instance).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={
        200: update_ticket_type_response,
        400: IMPOSSIBLE_UPDATE_STATUS,
        404: TICKET_TYPE_NOT_FOUND
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

        return Response(TicketTypeSerializer(instance).data, status=status.HTTP_200_OK)


class RouteViewSet(viewsets.GenericViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['route_number', 'name', 'revenue_type',
                        'tariff_type', 'route_type', 'secop_id',  'vehicle_type']
    ordering_fields = ['route_number', 'name']
    ordering = ['route_number']

    update_route_response = openapi.Response(SUCCESS_RESPONSE, RouteSerializer)

    def get_serializer_class(self):
        if self.action == 'create':
            return RouteSerializerCreate
        elif self.action == 'update':
            return RouteSerializerUpdate
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
        201: update_route_response,
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
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(responses={
        200: update_route_response,
        400: BAD_REQUEST,
        403: ACCESS_FORBIDDEN,
        404: NOT_FOUND
    })
    @admin_required
    def update(self, request, *args, **kwargs):
        """
        Доступно только администратору
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(RouteSerializer(instance).data, status=status.HTTP_200_OK)


class AdminViewSet(
        viewsets.GenericViewSet):
    REFRESHTOKEN_COOKIE = 'REFRESHTOKEN'

    queryset = User.objects.all()
    serializer_class = LoginSerializer

    refresh_password_response = openapi.Response(SUCCESS_RESPONSE, UserSerializerResponse)

    def get_queryset(self):
        if self.request.user.user.role in (UserRole.AGENT, UserRole.CARRIER):
            company = self.request.user.user.company
            return company.users.all()
        elif self.request.user.user.role in (UserRole.ADMIN, UserRole.SECURITY_ADMIN):
            return self.queryset

    def __set_refreshtoken_cookie(self, response, refresh_token):
        response.set_cookie(
            self.REFRESHTOKEN_COOKIE,
            value=refresh_token,
            secure=True,
            httponly=True,
        )

    def __delete_refreshtoken_cookie(self, response):
        response.delete_cookie(self.REFRESHTOKEN_COOKIE)

    def __get_credentials_response(self, user, refresh_token=None):
        if refresh_token is None:
            refresh_token = RefreshToken.for_user(user.auth_user)

        serializer = CredentialsSerializer(data={
            'access_token': str(refresh_token.access_token),
            'expires': datetime.utcfromtimestamp(refresh_token['exp']),
            'user_id': user.pk
        })

        if not serializer.is_valid():
            raise RuntimeError(serializer.errors)

        response = Response(serializer.validated_data)
        self.__set_refreshtoken_cookie(response, str(refresh_token))

        return response

    @action(
        detail=False,
        methods=['post'],
        serializer_class=LoginSerializer,
        permission_classes=(AllowAny,),
    )
    def login(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        current_user = User.objects.filter(
            login=serializer.validated_data['login']
        ).first()
        if not current_user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        password = current_user.hash_password(
            serializer.validated_data['password'],
        )

        auth_user = authenticate(
            request=request,
            username=current_user.id,
            password=password
        )
        if auth_user is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        return self.__get_credentials_response(current_user)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(AllowAny,),
        url_path='refresh-token',
    )
    def refresh_token(self, request, **kwargs):
        refresh_token = self.request.COOKIES.get(self.REFRESHTOKEN_COOKIE)

        refresh = RefreshToken(refresh_token)
        user_id = refresh.get(api_settings.USER_ID_CLAIM)
        if user_id is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        user = User.objects \
            .filter(auth_user=user_id) \
            .first()
        if user is None or user.status != UserStatus.ACTIVE:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        refresh.set_jti()
        refresh.set_exp()

        return self.__get_credentials_response(user, refresh_token=refresh)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(AllowAny,),
        url_path='revoke-token',
    )
    def revoke_token(self, request, **kwargs):
        response = HttpResponse('', content_type='text/plain')
        self.__delete_refreshtoken_cookie(response)
        return response

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,),
        serializer_class=UserSerializerItem,
        url_path='me'
    )
    def get_current_user(self, request, **kwargs):
        """
        Информация о текущем юзере
        """
        serializer = self.get_serializer(instance=self.request.user.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={
        200: refresh_password_response,
        400: BAD_REQUEST,
        403: ACCESS_FORBIDDEN
    })
    @agent_carrier_required
    @action(
        detail=False,
        url_path='refresh-password',
        methods=['put'],
        serializer_class=SerializerRefreshPassword
    )
    def refresh_password(self, request, *args, **kwargs):
        """
        Обновляет пароль пользователю по переданному user_id.
        Доступно ролям АДМИН, ПЕРЕВОЗЧИК (только своим контроллерам), АГЕНТ (только своим точкам продажи)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.get_queryset().filter(id=serializer.validated_data['user_id']).first()
        if not user:
            raise ValidationError(USER_NOT_FOUND)

        new_password = get_random_string()
        password = get_hash_password(new_password)
        user.auth_user.set_password(user.hash_password(password))
        user.auth_user.save()
        data = {
            'user_id': user.id,
            'company_id': user.company.id,
            'login': user.login,
            'password': new_password
        }
        return Response(data=data, status=status.HTTP_200_OK)



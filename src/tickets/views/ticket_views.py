from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


from tickets.serializers import *
from tickets.services import configurator
from tickets.common.decorators import admin_required, seller_required, validator_required, inspector_required
from tickets.common.actions import complete_ticket, check_completed_ticket
from tickets.common.responses import TOKEN_NOT_FOUND, CREATE_TICKET_DESCRIPTION, \
    CREATE_TRIP_DESCRIPTION, LOAD_SUCCESS, SUCCESS_RESPONSE, STATUS_USER_NOT_ACTIVE, WORKDAY_NOT_FOUND


class TicketViewSet(viewsets.GenericViewSet, RetrieveModelMixin,):
    queryset = Ticket.objects.prefetch_related('operations').all()
    serializer_class = TicketSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['id', 'ticket_type', 'status', 'start_date', 'end_date', 'seller_id']
    ordering_fields = ['created', 'ticket_type', 'status', 'start_date', 'end_date', 'seller_id']
    ordering = ['created']

    create_ticket_response = openapi.Response(CREATE_TICKET_DESCRIPTION, TicketSerializerResponse)
    trip_response = openapi.Response(CREATE_TRIP_DESCRIPTION, TripSerializerSwagger)

    def get_serializer_class(self):
        if self.action == 'create':
            return TicketSerializerCreate
        elif self.action in ('list', 'retrieve'):
            return TicketSerializer
        elif self.action in ('load_trips',):
            return LoadTripsSerializer
        return self.serializer_class

    @admin_required
    def list(self, request, *args, **kwargs):
        """
        Массив билетов
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=TicketSerializerCreate, responses={
        201: create_ticket_response,
        400: TOKEN_NOT_FOUND
    })
    @seller_required
    def create(self, request, *args, **kwargs):
        """
        Продажа билета
        Передается токен идемпотентности и тип билета (по умолчанию - разовый)
        """
        seller = self.request.user.user
        if seller.status != UserStatus.ACTIVE:
            return Response(STATUS_USER_NOT_ACTIVE, status=status.HTTP_403_FORBIDDEN)
        ticket_type = request.data.get('ticket_type', TicketType.SINGLE)
        token = request.data.get('token')
        if not token:
            return Response(TOKEN_NOT_FOUND, status=status.HTTP_400_BAD_REQUEST)
        tm = configurator[ticket_type](seller=seller, token=token)
        data = tm.make_ticket_data()
        return Response(data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(request_body=TripSerializer, responses={
        200: trip_response
    })
    @validator_required
    @action(
        detail=False,
        methods=['post'],
        url_path='trip',
        serializer_class=TripSerializer
    )
    def create_trip(self, request, **kwargs):
        """
        Гашение разового билета, создание поездки
        """
        validator = self.request.user.user
        if not validator.current_workday:
            return Response(WORKDAY_NOT_FOUND, status=status.HTTP_400_BAD_REQUEST)

        serializer = TripSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = Ticket.objects.filter(
            id=serializer.validated_data.get('ticket').get('id')
        ).first()
        serializer.validated_data.pop('ticket')
        if ticket:
            if ticket.status == TicketStatus.ACTIVE:
                if ticket.end_date < datetime.now().date():
                    status_info = 'EXPIRED'
                    data = TicketStatus.check_statuses[status_info]
                    return Response(data=data, status=status.HTTP_200_OK)
                complete_ticket(ticket, serializer.validated_data, self.request.user.user)
                status_info = 'COMPLETED'
            elif ticket.status == TicketStatus.COMPLETED:
                status_info = check_completed_ticket(ticket, serializer.validated_data)
            elif ticket.status == TicketStatus.DISABLED:
                status_info = 'DISABLED'
        else:
            status_info = 'NOT_FOUND'
            data = TicketStatus.check_statuses[status_info]
            return Response(data=data, status=status.HTTP_200_OK)

        # TODO Логика подходит только для разового билета, потом переделать
        serializer = TripSerializerResponse(instance=ticket.operations.first())

        data = TicketStatus.check_statuses[status_info]
        data.update(serializer.data)
        return Response(data=data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=CheckTripSerializer, responses={
        200: trip_response
    })
    @inspector_required
    @action(
        detail=False,
        methods=['post'],
        url_path='check',
        serializer_class=CheckTripSerializer
    )
    def check_trip(self, request, **kwargs):
        """
        Проверка билета на гашение
        """

        serializer = CheckTripSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = Ticket.objects.filter(
            id=serializer.validated_data.get('ticket').get('id')
        ).first()
        serializer.validated_data.pop('ticket')

        if ticket:
            if ticket.status == TicketStatus.ACTIVE:
                if ticket.end_date < datetime.now().date():
                    status_info = 'EXPIRED'
                else:
                    status_info = 'ACTIVE'
                data = TicketStatus.check_statuses[status_info]
                return Response(data=data, status=status.HTTP_200_OK)
            elif ticket.status == TicketStatus.COMPLETED:
                status_info = check_completed_ticket(ticket, serializer.validated_data)
            elif ticket.status == TicketStatus.DISABLED:
                status_info = 'DISABLED'
                data = TicketStatus.check_statuses[status_info]
                return Response(data=data, status=status.HTTP_200_OK)
        else:
            status_info = 'NOT_FOUND'
            data = TicketStatus.check_statuses[status_info]
            return Response(data=data, status=status.HTTP_200_OK)

        serializer = TripSerializerResponse(instance=ticket.operations.first())
        data = TicketStatus.check_statuses[status_info]
        data.update(serializer.data)
        return Response(data=data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=LoadTripsSerializer, responses={
        200: openapi.Response(LOAD_SUCCESS)
    })
    @validator_required
    @action(
        detail=False,
        methods=['post'],
        url_path='load-trips',
        serializer_class=LoadTripsSerializer
    )
    def load_trips(self, request, **kwargs):
        """
        Гашение билетов, создание поездок
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for item in serializer.validated_data['tickets']:
            ticket = Ticket.objects.filter(
                id=item.get('ticket').get('id')
            ).first()
            item.pop('ticket')
            if ticket and ticket.status == TicketStatus.ACTIVE:
                complete_ticket(ticket, item, self.request.user.user)

        return Response(status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={
        200: openapi.Response(SUCCESS_RESPONSE)
    })
    @action(
        detail=False,
        methods=['post'],
        url_path='ping'
    )
    def ping(self, request, **kwargs):
        """
        Проверка связи с сервером
        """
        return Response(status=status.HTTP_200_OK)

    @admin_required
    @action(
        detail=False,
        methods=['post'],
        url_path='test-tickets'
    )
    def load_tickets(self, request, **kwargs):
        """
        Запрос для генерации тестовых билетов
        """
        from tickets.common.actions import create_test_tickets
        data = create_test_tickets()

        return Response(data=data, status=status.HTTP_200_OK)


class OperationViewSet(viewsets.GenericViewSet, RetrieveModelMixin, ):
    queryset = Operation.objects.all()
    serializer_class = OperationSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['id', 'ticket', 'operation_type', 'route_number', 'run_number', 'vehicle_type',
                        'vehicle_number', 'license_plate', 'validator_number',
                        'validator_type']
    ordering_fields = ['created', 'id', 'operation_type', 'vehicle_type', 'route_number', 'run_number']
    ordering = ['-created']

    @admin_required
    def list(self, request, *args, **kwargs):
        """
        Массив поездок
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)



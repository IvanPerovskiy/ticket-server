from rest_framework import serializers

from tickets.models import *
from tickets.common.responses import IMPOSSIBLE_UPDATE_TARIFF, TARIFF_HAVE_TICKETS


class TicketSerializerCreate(serializers.Serializer):
    """
    Токен идемпотентности и тип билета (по умолчанию - разовый)
    """
    token = serializers.CharField()
    ticket_type = serializers.IntegerField(default=1)


class TicketSerializerResponse(serializers.Serializer):
    ticket_name = serializers.CharField()
    series = serializers.CharField()
    number = serializers.CharField()
    company_name = serializers.CharField()
    agent_name = serializers.CharField()
    vehicle_type = serializers.IntegerField()
    created_date = serializers.CharField()
    start_date = serializers.CharField()
    end_date = serializers.CharField()
    ticket_zone = serializers.CharField()
    amount = serializers.DecimalField(decimal_places=2, max_digits=20)
    qr_code = serializers.CharField()


class TripSerializer(serializers.ModelSerializer):
    ticket_id = serializers.UUIDField(source='ticket.id', required=True)
    vehicle_type = serializers.IntegerField(source='vehicle_type.number', required=True)

    class Meta:
        model = Operation
        fields = ('ticket_id', 'run_number', 'created', 'validator_number',
                  'route_number', 'vehicle_type', 'vehicle_number',
                  'license_plate')
        extra_kwargs = {
            'ticket_id': {'required': True},
            'created': {'required': True},
            'validator_number': {'required': True},
            'run_number': {'required': True},
            'vehicle_number': {'required': True},
            'route_number': {'required': True},
            'vehicle_type': {'required': True},
            'license_plate': {'required': False}
        }


class TicketSerializer(serializers.ModelSerializer):
    trips = TripSerializer(many=True, source='operations')

    class Meta:
        model = Ticket
        fields = ('id', 'series', 'seller', 'ticket_type', 'status',
                  'amount', 'created', 'completed', 'disabled',
                  'start_date', 'end_date', 'trips')


class TicketSerializerList(serializers.Serializer):
    count = models.IntegerField()
    tickets = TicketSerializer(many=True)


class TripSerializerResponse(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = ('created', 'vehicle_type', 'run_number',
                  'route_number', 'vehicle_number')


class OperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = ('id', 'ticket', 'operation_type', 'route_number', 'run_number', 'vehicle_type', 'vehicle_number',
                  'license_plate', 'validator_number', 'validator_type', 'created',
                  'imported')


class TripSerializerSwagger(TripSerializerResponse):
    """
    Сериалайзеры Swagger используются только для правильной автодокументации
    """
    code = serializers.ChoiceField(choices=[ts['code'] for ts in TicketStatus.check_statuses.values()])
    detail = serializers.ChoiceField(choices=[ts['detail'] for ts in TicketStatus.check_statuses.values()])

    class Meta:
        model = Operation
        fields = ('code', 'detail', 'created', 'vehicle_type', 'run_number',
                  'route_number', 'vehicle_number')


class LoadTripsSerializer(serializers.Serializer):
    tickets = TripSerializer(many=True)


class CheckTripSerializer(serializers.ModelSerializer):
    ticket_id = serializers.UUIDField(source='ticket.id', required=True)
    carrier_code = serializers.IntegerField(required=True)
    vehicle_type = serializers.IntegerField(source='vehicle_type.number', required=False)

    class Meta:
        model = Operation
        fields = ('ticket_id', 'run_number', 'carrier_code',
                  'route_number', 'vehicle_type', 'vehicle_number',
                  'validator_number', 'validator_type')

        extra_kwargs = {
            'ticket_id': {'required': True},
            'carrier_code': {'required': True},
            'run_number': {'required': False},
            'route_number': {'required': False},
            'vehicle_type': {'required': False},
            'vehicle_number': {'required': True},
            'validator_number': {'required': False},
            'validator_type': {'required': False}
        }


class WorkdayOpenSerializer(serializers.Serializer):
    workday_id = serializers.UUIDField()
    pub_key = serializers.CharField()


class WorkdayCloseSerializer(serializers.Serializer):
    workday_id = serializers.UUIDField()
    pub_key = serializers.CharField()
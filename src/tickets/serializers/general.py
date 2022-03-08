from rest_framework import serializers

from tickets.models import *
from tickets.common.responses import IMPOSSIBLE_UPDATE_TARIFF, TARIFF_HAVE_TICKETS, USER_NOT_FOUND, \
    SETTING_ALREADY_CREATED


class TicketTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketType
        fields = '__all__'


class TicketTypeSerializerUpdate(serializers.ModelSerializer):
    class Meta:
        model = TicketType
        fields = ('name', 'start_date', 'end_date', 'code')
        extra_kwargs = {
            'name': {'required': False},
            'start_date': {'required': False},
            'end_date': {'required': False},
            'code': {'required': False},
            'status': {'required': False}
        }

    def validate(self, data):
        if self.instance.start_date < date.today():
            raise ValidationError(IMPOSSIBLE_UPDATE_TARIFF)
        if 'start_date' in data or 'cost' in data or 'status' in data:
            if tariff := self.instance:
                if tariff.get_count_tickets() > 0:
                    raise ValidationError(TARIFF_HAVE_TICKETS)
        return data


class TariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = '__all__'


class TariffSerializerUpdate(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = ('name', 'start_date', 'end_date', 'cost', 'status')
        extra_kwargs = {
            'name': {'required': False},
            'start_date': {'required': False},
            'end_date': {'required': False},
            'cost': {'required': False}
        }

    def validate(self, data):
        if 'start_date' in data or 'cost' in data or 'status' in data:
            if tariff := self.instance:
                if tariff.get_count_tickets() > 0:
                    raise ValidationError(IMPOSSIBLE_UPDATE_TARIFF)
        return data


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = '__all__'


class SettingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = ('value',)


class SettingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = ('name', 'value', 'description')

    def validate(self, data):
        setting = Setting.objects.filter(name=data.get('name')).first()
        if setting:
            raise ValidationError(SETTING_ALREADY_CREATED)
        return data


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ('id', 'vehicle_type', 'route_number', 'name', 'revenue_type',
                  'tariff_type', 'route_type', 'secop_id', 'route_detail', 'carriers')


class RouteSerializerUpdate(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ('vehicle_type', 'route_number', 'name', 'revenue_type',
                  'tariff_type', 'route_type', 'secop_id', 'route_detail', 'carriers')
        extra_kwargs = {
            'vehicle_type': {'required': False},
            'name': {'required': False},
            'route_number': {'required': False},
            'revenue_type': {'required': False},
            'tariff_type': {'required': False},
            'route_type': {'required': False},
            'secop_id': {'required': False},
            'route_detail': {'required': False}
        }

    def update(self, instance, validated_data):
        if 'carriers' in validated_data:
            carriers = validated_data.pop('carriers')
            for carrier in carriers:
                instance.carriers.add(carrier)
            instance.save()
            carriers = set(carriers)
            route_carriers = set(instance.carriers.all())

            for carrier in route_carriers.difference(carriers):
                instance.carriers.remove(carrier)
        return super(RouteSerializerUpdate, self).update(instance, validated_data)


class RouteSerializerCreate(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ('vehicle_type', 'route_number', 'name', 'revenue_type',
                  'tariff_type', 'route_type', 'secop_id', 'route_detail', 'carriers')
        extra_kwargs = {
            'vehicle_type': {'required': True},
            'name': {'required': False},
            'route_number': {'required': True},
            'revenue_type': {'required': False},
            'tariff_type': {'required': False},
            'route_type': {'required': False},
            'secop_id': {'required': False},
            'route_detail': {'required': False}
        }


class SerializerUpdateStatus(serializers.Serializer):
    status = serializers.IntegerField(required=True)

    def update(self, instance, validated_data):
        instance.set_status(validated_data['status'])
        instance.save()
        return instance


class SerializerRefreshPassword(serializers.Serializer):
    user_id = serializers.UUIDField(required=True)

    def validate(self, data):
        user = User.objects.filter(id=data['user_id']).first()
        if not user:
            raise ValidationError(USER_NOT_FOUND)
        return data


class SettingTypeSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    name = serializers.CharField()

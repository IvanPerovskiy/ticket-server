from rest_framework import serializers

from tickets.models import *


class LoginSerializer(serializers.Serializer):
    login = serializers.CharField()
    password = serializers.CharField()


class CredentialsSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    expires = serializers.DateTimeField()
    user_id = serializers.UUIDField()


class UserSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    login = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    address = serializers.CharField(required=False)
    password = serializers.CharField(required=False)


class UserCreateSerializer(serializers.Serializer):
    company_id = serializers.UUIDField(required=False)
    code = serializers.IntegerField()
    login = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    address = serializers.CharField(required=False)
    password = serializers.CharField(required=False)


class UsersCreateSerializer(serializers.Serializer):
    company_id = serializers.UUIDField(required=False)
    file = serializers.Field()


class UsersSerializerResponse(serializers.Serializer):
    count_error_items = serializers.IntegerField()
    count_double_items = serializers.IntegerField()
    count_created_items = serializers.IntegerField()
    file = serializers.Field()


class UserSerializerResponse(serializers.Serializer):
    user_id = serializers.UUIDField()
    company_id = serializers.UUIDField()
    login = serializers.CharField(required=False)
    password = serializers.CharField(required=False)


class CompanySerializer(serializers.Serializer):
    inn = serializers.CharField()
    code = serializers.IntegerField(required=False)
    name = serializers.CharField(required=False)


class UserCompanyCreateSerializer(serializers.Serializer):
    user = UserSerializer()
    company = CompanySerializer()


# -- Агент ---


class AgentCreateSerializer(serializers.Serializer):
    inn = serializers.CharField()
    code = serializers.IntegerField(required=False)
    name = serializers.CharField(required=False)
    ticket_types = serializers.ListField(child=serializers.IntegerField(), required=False)


class UserAgentCreateSerializer(serializers.Serializer):
    user = UserSerializer()
    company = AgentCreateSerializer()


class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'login', 'name', 'code', 'company_id', 'status', 'role', 'address', 'position')


class UserSerializerItem(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'login', 'name', 'code', 'company_id', 'status', 'role', 'address', 'position')


class AgentSerializer(serializers.ModelSerializer):
    sellers = SellerSerializer(many=True, source='users')

    class Meta:
        model = Company
        fields = ('id', 'inn', 'name', 'code', 'status', 'ticket_types', 'company_form', 'secop_id', 'short_name',
                  'director', 'position', 'sign_doc', 'ogrn', 'kpp', 'registration_address', 'actual_address',
                  'correspondence_address', 'bic', 'bank', 'correspondent_account', 'account', 'agent_fee',
                  'agent_fee_percent', 'service_fee', 'service_fee_percent', 'sellers')


class AgentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ('inn', 'name', 'code', 'ticket_types', 'company_form', 'secop_id', 'short_name',
                  'director', 'position', 'sign_doc', 'ogrn', 'kpp', 'registration_address', 'actual_address',
                  'correspondence_address', 'bic', 'bank', 'correspondent_account', 'account', 'agent_fee',
                  'agent_fee_percent', 'service_fee', 'service_fee_percent')
        extra_kwargs = {
            'inn': {'required': False},
            'name': {'required': False},
            'code': {'required': False},
            'ticket_types': {'required': False},
            'company_form': {'required': False},
            'secop_id': {'required': False},
            'short_name': {'required': False},
            'director': {'required': False},
            'position': {'required': False},
            'sign_doc': {'required': False},
            'ogrn': {'required': False},
            'kpp': {'required': False},
            'registration_address': {'required': False},
            'actual_address': {'required': False},
            'correspondence_address': {'required': False},
            'bic': {'required': False},
            'bank': {'required': False},
            'correspondent_account': {'required': False},
            'account': {'required': False},
            'agent_fee': {'required': False},
            'agent_fee_percent': {'required': False},
            'service_fee': {'required': False},
            'service_fee_percent': {'required': False}
        }

    def update(self, instance, validated_data):
        if 'ticket_types' in validated_data:
            from tickets.common.actions import add_ticket_types_for_agent

            add_ticket_types_for_agent(instance, validated_data['ticket_types'])
            validated_data.pop('ticket_types')
            instance.save()

        return super(AgentUpdateSerializer, self).update(instance, validated_data)


# -- Перевозчики ---


class CarrierCreateSerializer(serializers.Serializer):
    inn = serializers.CharField()
    code = serializers.IntegerField(required=False)
    name = serializers.CharField(required=False)
    vehicle_types = serializers.ListField(child=serializers.IntegerField())
    sign_doc = serializers.CharField(required=False)


class UserCarrierCreateSerializer(serializers.Serializer):
    user = UserSerializer()
    company = CarrierCreateSerializer()


class CarrierUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ('inn', 'name', 'code', 'vehicle_types', 'company_form', 'secop_id',
                  'short_name', 'director', 'position', 'sign_doc', 'ogrn', 'kpp',
                  'registration_address', 'actual_address', 'correspondence_address', 'bic', 'bank',
                  'correspondent_account', 'account')
        extra_kwargs = {
            'inn': {'required': False},
            'name': {'required': False},
            'code': {'required': False},
            'vehicle_types': {'required': False},
            'company_form': {'required': False},
            'secop_id': {'required': False},
            'short_name': {'required': False},
            'director': {'required': False},
            'position': {'required': False},
            'sign_doc': {'required': False},
            'ogrn': {'required': False},
            'kpp': {'required': False},
            'registration_address': {'required': False},
            'actual_address': {'required': False},
            'correspondence_address': {'required': False},
            'bic': {'required': False},
            'bank': {'required': False},
            'correspondent_account': {'required': False},
            'account': {'required': False}
        }

    def update(self, instance, validated_data):
        if 'vehicle_types' in validated_data:
            from tickets.common.actions import add_vehicle_types_for_carrier

            add_vehicle_types_for_carrier(instance, validated_data['vehicle_types'])
            validated_data.pop('vehicle_types')
            instance.save()

        return super(CarrierUpdateSerializer, self).update(instance, validated_data)


class InspectorSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = '__all__'


class CarrierSerializer(serializers.ModelSerializer):
    inspectors = InspectorSerializer(many=True, source='users')

    class Meta:
        model = Company
        fields = ('id', 'inn', 'name', 'code', 'status', 'vehicle_types', 'company_form', 'secop_id',
                  'short_name', 'director', 'position', 'sign_doc', 'ogrn', 'kpp',
                  'registration_address', 'actual_address', 'correspondence_address', 'bic', 'bank',
                  'correspondent_account', 'account', 'inspectors')




import base64
import hashlib
import uuid

from datetime import datetime, date

from django.db import transaction
from django.conf import settings
from django.db import models
from django.utils import safestring, timezone
from rest_framework.exceptions import ValidationError

from tickets.models.types import *
from tickets.models.statuses import *


class VehicleType(models.Model):
    name = models.CharField(max_length=30)
    number = models.IntegerField(unique=True, db_index=True)


class TicketType(models.Model):
    tariff = models.ForeignKey('Tariff', on_delete=models.CASCADE, related_name='tariff_ticket_types')
    zone = models.ForeignKey('Zone', on_delete=models.CASCADE, related_name='ticket_types')
    code = models.CharField(max_length=10, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    lifetime = models.PositiveIntegerField(null=True, blank=True)
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(null=True, blank=True)
    vehicle_types = models.ManyToManyField(VehicleType)
    created = models.DateTimeField(auto_now_add=True)
    number = models.IntegerField()
    agent_permission = models.BooleanField(default=False)
    status = models.IntegerField(choices=TicketTypeStatus.choices, default=TicketTypeStatus.ACTIVE)

    SINGLE = 1

    def get_repr_vehicle_types(self):
        return '-'.join([vehicle_type.name for vehicle_type in self.vehicle_types.all()])

    def get_repr_vehicle_type_numbers(self):
        return '-'.join([str(vehicle_type.number) for vehicle_type in self.vehicle_types.all()])

    def get_count_tickets(self):
        return len(
            self.tickets.all()
        )

    def set_status(self, status):
        self.status = status
        self.save()


class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    login = models.CharField(max_length=100)
    name = models.CharField(max_length=200, null=True, blank=True)
    code = models.IntegerField(null=True, blank=True)
    position = models.CharField(max_length=200)                     # Должность
    auth_user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    salt = models.CharField(max_length=200)
    status = models.IntegerField(choices=UserStatus.choices)
    role = models.IntegerField(choices=UserRole.choices)
    address = models.CharField(null=True, blank=True, max_length=250)

    @property
    def current_workday(self):
        return self.workdays.filter(status=WorkdayStatus.OPEN).first()

    def hash_password(self, password):
        h = hashlib.sha256()
        h.update(password.encode('utf-8'))
        h.update(self.salt.encode('utf-8'))
        return h.hexdigest()

    def set_status(self, status):
        if self.status == UserStatus.DELETED:
            raise ValidationError('Нельзя поменять статус удаленного пользователя')
        elif status == UserStatus.NEW:
            raise ValidationError('Нельзя поменять статус на Новый')

        with transaction.atomic():
            self.status = status
            self.save()

    class Meta():
        verbose_name = 'Пользователь'
        verbose_name_plural = "Пользователи"


class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.IntegerField(null=True)
    category = models.IntegerField(choices=CompanyCategory.choices)
    company_form = models.CharField(max_length=200, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    secop_id = models.CharField(max_length=12, null=True, blank=True)
    short_name = models.CharField(max_length=100, null=True, blank=True)

    director = models.CharField(max_length=200, null=True, blank=True)
    position = models.CharField(max_length=200, null=True, blank=True)
    sign_doc = models.CharField(max_length=200, null=True, blank=True)

    inn = models.CharField(max_length=12, null=True, blank=True, unique=True)
    ogrn = models.CharField(max_length=15, null=True, blank=True)
    kpp = models.CharField(max_length=9, null=True, blank=True)

    status = models.IntegerField(choices=CompanyStatus.choices, default=CompanyStatus.ACTIVE)

    registration_address = models.CharField(max_length=200, null=True, blank=True)
    actual_address = models.CharField(max_length=200, null=True, blank=True)
    correspondence_address = models.CharField(max_length=200, null=True, blank=True)

    bic = models.CharField(max_length=9, null=True, blank=True)
    bank = models.CharField(max_length=9, null=True, blank=True)
    correspondent_account = models.CharField(max_length=100, null=True, blank=True)
    account = models.CharField(max_length=100, null=True, blank=True)

    agent_fee = models.DecimalField(decimal_places=2, max_digits=20, default='0.00')
    agent_fee_percent = models.BooleanField(default=False)
    service_fee = models.DecimalField(decimal_places=2, max_digits=20, default='0.00')
    service_fee_percent = models.BooleanField(default=False)

    ticket_types = models.ManyToManyField(TicketType, blank=True)
    vehicle_types = models.ManyToManyField(VehicleType, blank=True)

    def set_status(self, status):
        if self.status == CompanyStatus.DELETED:
            raise ValidationError('Нельзя поменять статус удаленной компании')
        elif status == CompanyStatus.NEW:
            raise ValidationError('Нельзя поменять статус на Новый')

        with transaction.atomic():
            for user in self.users.all():
                user.set_status(status)
                self.status = status
            self.save()

    class Meta():
        verbose_name = 'Организация'
        verbose_name_plural = 'Организации'


class Contract(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.CharField(max_length=100)
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='contracts')
    start_date = models.DateField(null=True, blank=True, default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=False)


class Device(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    maker = models.CharField(max_length=200)
    model_name = models.CharField(max_length=100)
    factory_number = models.CharField(max_length=100)
    series_number = models.CharField(max_length=100)
    device_type = models.IntegerField(choices=DeviceType.choices)
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='devices')
    validator = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='device', blank=True, null=True
    )
    created = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=DeviceStatus.choices, default=DeviceStatus.ACTIVE)
    status_updated = models.DateTimeField(null=True, blank=True)
    last_transaction_date = models.DateTimeField(null=True, blank=True)

    class Meta():
        verbose_name = 'Валидатор'
        verbose_name_plural = 'Валидаторы'


class Route(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle_type = models.ForeignKey(
        'VehicleType', on_delete=models.CASCADE, related_name='vehicle_type_routes'
    )
    route_number = models.IntegerField(db_index=True)
    name = models.CharField(max_length=25, blank=True, null=True)
    revenue_type = models.IntegerField(choices=RevenueType.choices, default=RevenueType.NOT_DISTRIBUTED)
    tariff_type = models.IntegerField(choices=TariffType.choices, default=TariffType.CONSTANT)
    route_type = models.IntegerField(choices=RouteType.choices, default=RouteType.MUNICIPAL)

    secop_id = models.CharField(max_length=12, blank=True)
    route_detail = models.TextField(blank=True, null=True)

    carriers = models.ManyToManyField('Company', related_name='routes', blank=True)
    transfer_routes = models.ManyToManyField('Route', blank=True)

    class Meta():
        verbose_name = 'Маршрут'
        verbose_name_plural = 'Маршруты'


class Zone(models.Model):
    name = models.CharField(max_length=300)
    number = models.IntegerField(unique=True, db_index=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    routes = models.ManyToManyField(Route)


class Tariff(models.Model):
    name = models.CharField(max_length=200)
    number = models.IntegerField(unique=True, db_index=True)
    cost = models.DecimalField(decimal_places=2, max_digits=20)
    created = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.IntegerField(choices=TariffStatus.choices, default=TariffStatus.ACTIVE)

    def get_count_tickets(self):
        return len(
            Ticket.objects.select_related(
                'ticket_type').select_related(
                'ticket_type__tariff').filter(
                ticket_type__tariff_id=self.id
            ).all()
        )

    def set_status(self, status):
        self.status = status
        self.save()


class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=250)     # Токен идемпотентности
    series = models.CharField(max_length=8, null=True, blank=True)

    seller = models.ForeignKey('User', on_delete=models.CASCADE, related_name='tickets', null=True, blank=True)
    status = models.IntegerField(choices=TicketStatus.choices, default=TicketStatus.ACTIVE)
    ticket_type = models.ForeignKey('TicketType', on_delete=models.CASCADE, related_name='tickets')
    amount = models.DecimalField(decimal_places=2, max_digits=20)

    created = models.DateTimeField(auto_now_add=True)
    completed = models.DateTimeField(blank=True, null=True)
    disabled = models.DateTimeField(blank=True, null=True)

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    qr_code = models.BinaryField(blank=True, null=True)

    class Meta():
        verbose_name = 'Билет'
        verbose_name_plural = 'Билеты'

    @property
    def agent_name(self):
        return self.seller.company.name

    @property
    def agent_code(self):
        return self.seller.company.code

    @property
    def agent_inn(self):
        return self.seller.company.inn

    def set_status(self, status):
        if self.status == TicketStatus.ACTIVE and status == TicketStatus.COMPLETED:
            self.completed = datetime.now()
        elif self.status == TicketStatus.COMPLETED and status == TicketStatus.DISABLED:
            self.disabled = datetime.now()
        self.status = status
        self.save()

    def image_base64(self):
        if self.qr_code:
            return base64.b64encode(self.qr_code)
        return None

    def image_tag(self):
        img = self.image_base64()
        if img:
            tag = '<img src="data:image/png;base64, {}" style="max-width:300px">'.format(img)
            return safestring.mark_safe(tag)
        return 'Error image'


class TicketNumber(models.Model):
    """
    Отдельная таблица сделана для получения автоинкрементного номера билета
    """
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='number')


class Operation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='operations')
    operation_type = models.IntegerField(choices=OperationType.choices, default=OperationType.TRIP)

    route_number = models.CharField(max_length=25, blank=True, null=True)       # Номер маршрута
    run_number = models.CharField(max_length=25, blank=True, null=True)         # Номер рейса
    vehicle_type = models.ForeignKey(
        VehicleType, on_delete=models.PROTECT, related_name='vehicle_type_operations', blank=True, null=True
    )                                                                           # Тип ТС
    vehicle_number = models.CharField(max_length=25, blank=True, null=True)     # Бортовой номер ТС
    license_plate = models.CharField(max_length=25, blank=True, null=True)      # ГРЗ

    workday = models.ForeignKey(
        'WorkDay', on_delete=models.CASCADE, related_name='trips', blank=True, null=True
    )                                                                           # Смена валидатора, погасившего билет

    # Номер валидатора, должен совпадать с кодом валидатора, как пользователя
    validator_number = models.IntegerField(blank=True, null=True)                # Номер валидатора
    validator_type = models.CharField(max_length=1, blank=True, null=True)       # Тип валидатора

    created = models.DateTimeField()                                             # Время гашения
    imported = models.DateTimeField(auto_now_add=True)                           # Время загрузки на сервер

    class Meta():
        verbose_name = 'Операция'
        verbose_name_plural = 'Операции'

    @property
    def carrier(self):
        return self.workday.validator.company


class Workday(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    validator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='workdays', blank=True, null=True
    )
    created = models.DateTimeField(auto_now_add=True)
    closed = models.DateTimeField(blank=True, null=True)
    status = models.IntegerField(choices=WorkdayStatus.choices, default=WorkdayStatus.OPEN)


class Setting(models.Model):
    name = models.CharField(unique=True, max_length=100)
    value = models.CharField(max_length=300, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta():
        verbose_name = 'Настройка'
        verbose_name_plural = 'Настройки'










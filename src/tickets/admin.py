from django.contrib import admin
from django.conf import settings
from django.utils.html import format_html

from tickets.models import *
from tickets.models.statuses import TicketStatus


class TicketAdmin(admin.ModelAdmin):
    model = Ticket
    list_display = (
        'created', 'id', 'status', 'qr', 'ticket_stage'
    )

    readonly_fields = ['id', 'created', 'completed', 'disabled']
    fields = ['id', 'series', 'seller', 'status', 'amount', 'created',
              'completed', 'disabled', 'start_date', 'end_date']

    @admin.display(empty_value='???')
    def ticket_stage(self, obj):
        if obj.end_date < datetime.now().date():
            return 'Просрочен'
        elif obj.status == TicketStatus.ACTIVE:
            return 'Активный'
        elif obj.status == TicketStatus.COMPLETED:
            run_number = obj.operations.first().run_number
            return 'Погашен, рейс № {}'.format(run_number)
        elif obj.status == TicketStatus.DISABLED:
            return 'Не валиден'
        return obj.status

    @admin.display(empty_value='???')
    def qr(self, obj):
        return format_html('<a href=http://{}/api/uploads/{}.png>Код</a>',settings.DOMAIN, obj.id)


class UserAdmin(admin.ModelAdmin):
    model = User
    list_display = (
        'login', 'name', 'code', 'status', 'role'
    )


class SettingAdmin(admin.ModelAdmin):
    model = Setting
    list_display = (
        'name', 'value'
    )


class RouteAdmin(admin.ModelAdmin):
    model = Route
    list_display = (
        'route_number', 'name', 'vehicle_type'
    )


class OperationAdmin(admin.ModelAdmin):
    model = Operation
    list_display = (
        'run_number', 'route_number', 'operation_type'
    )


class CompanyAdmin(admin.ModelAdmin):
    model = Company
    list_display = (
        'name', 'inn', 'category'
    )


admin.site.register(User, UserAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Setting, SettingAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(Operation, OperationAdmin)
admin.site.register(Route, RouteAdmin)
admin.site.register(Device)
admin.site.register(VehicleType)
admin.site.register(TicketType)
admin.site.register(Contract)
admin.site.register(Zone)
admin.site.register(Tariff)
admin.site.register(Workday)

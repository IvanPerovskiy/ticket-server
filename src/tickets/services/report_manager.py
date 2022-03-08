"""
Created on 24.08.2021

:author: Ivan Perovsky
Генератор отчетов в csv и xlsx формате
"""
import os
import pandas as pd

from decimal import Decimal
from datetime import timedelta, datetime, time

from django.conf import settings
from django.db.models import Sum
from rest_framework.exceptions import ValidationError

from tickets.models import *
from tickets.common.utils import get_local_current_date, get_local_current_date_string, \
    timezone_converter, parse_datetime, format_datetime, get_local_current_datetime_string, \
    get_date_string


'''def generate_report(user, params, **kwargs):
    """
    Генерирует нужный отчет в зависимости от переданных параметров
    """
    report_type = kwargs.get('report_type')
    a = None
    if report_type == ReportType.SIMPLE:
        if user.role == UserRole.CLIENT_ADMIN:
            a = ClientOperationReportManager(user, params, **kwargs)
        elif user.role in (UserRole.MERCHANT_ADMIN, UserRole.OPERATOR_ADMIN):
            a = OperationReportManager(user, params, **kwargs)
    elif report_type == ReportType.JOURNEY:
        if user.role == UserRole.CLIENT_ADMIN:
            a = ClientJourneyReportManager(user, params, **kwargs)
        elif user.role in (UserRole.MERCHANT_ADMIN, UserRole.OPERATOR_ADMIN):
            a = JourneyReportManager(user, params, **kwargs)
    elif report_type == ReportType.DEFAULT:
        if user.role in (UserRole.MERCHANT_ADMIN, UserRole.OPERATOR_ADMIN):
            a = DefaultReportManager(user)
    elif report_type == ReportType.JOURNEY:
        if user.role == UserRole.CLIENT_ADMIN:
            a = ClientJourneyReportManager(user, params, **kwargs)
        elif user.role in (UserRole.MERCHANT_ADMIN, UserRole.OPERATOR_ADMIN):
            a = JourneyReportManager(user, params, **kwargs)
    elif report_type == ReportType.SINGLE_CLIENT:
        if not params.get('client'):
            raise ValidationError({
                'client': ['Не найден идентификатор клиента']
            })
        if user.role in (UserRole.MERCHANT_ADMIN, UserRole.OPERATOR_ADMIN):
            a = SingleClientReportManager(user, params, **kwargs)
    elif report_type == ReportType.SIMPLE_CLIENTS:
        if user.role in (UserRole.MERCHANT_ADMIN, UserRole.OPERATOR_ADMIN):
            a = ClientsReportManager(user, params, **kwargs)
    elif report_type == ReportType.SIMPLE_LABELS:
        if user.role in (UserRole.MERCHANT_ADMIN, UserRole.OPERATOR_ADMIN):
            a = LabelsReportManager(user, params, **kwargs)

    if not a:
        return None, None

    return a.generate()


class ReportManager:
    """
    Менеджер отчетов
    """
    def __init__(self, user, params, **kwargs):
        self.user = user
        self.path = kwargs.get('path', settings.MEDIA_ROOT)
        self.link = ''.join([settings.DOMAIN, settings.MEDIA_URL])
        self.format = kwargs.get('format', 'xlsx')
        self.timezone = settings.CELERY_TIMEZONE
        self.date_from = params.get('date_from', get_local_current_date() - timedelta(days=365))
        self.date_to = params.get('date_to', get_local_current_date())

        self.style_settings = {
            'title': {
                'align': 'center',
                'bold': True,
                'text_wrap': False,
                'valign': 'top',
                'fg_color': 'white',
                'font_size': 14
            },
            'subtitle': {
                'font_size': 11,
                'bold': False,
                'text_wrap': False,
                'valign': 'top',
            },
            'client': {
                'align': 'center',
                'font_size': 11,
                'bottom': 1,
                'text_wrap': False,
                'valign': 'top',
            },
            'header': {
                'align': 'center',
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            },
            'normal': {
                'align': 'center',
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            },
            'summary_text': {
                'align': 'left',
                'text_wrap': False,
                'valign': 'top',
                'border': 1
            },
            'summary_data': {
                'align': 'right',
                'text_wrap': False,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            }
        }

        # -- Параметры наследников ---
        self.startrow = 5  # Ряд начала таблицы
        self.title_params = {}
        self.fields = []
        self.index_label = '№ п/п'
        self.sheet_name = 'Отчет'
        self.columns = []
        self.file_name = self.get_file_name()
        self.params = params

    def generate(self):
        if not os.path.exists(self.path):
            os.mkdir(self.path)

        path = '{}{}.{}'.format(
            self.path,
            self.file_name,
            self.format
        )
        # Генерируем xlsx файл
        df = self.get_dataframe()

        if self.format == 'xlsx':
            writer = pd.ExcelWriter(
                path,
                engine='xlsxwriter',
                datetime_format='mmm d yyyy hh:mm:ss',
                date_format='mmmm dd yyyy'
            )
            # Convert the dataframe to an XlsxWriter Excel object.
            df.to_excel(
                writer,
                sheet_name='Sheet1',
                startrow=self.startrow+1,
                startcol=1,
                header=False,
                index_label=self.index_label,
                index=None
            )

            workbook = writer.book
            worksheet = writer.sheets['Sheet1']
            worksheet.set_column(0, 0, 4)
            for i in range(len(self.columns)):
                worksheet.set_column(i+1, i+1, self.columns[i]['width'])

            self.formats = self.add_formats(workbook)
            worksheet.write(self.startrow, 0, self.index_label, self.formats['header_format'])
            for i in range(len(df)):
                worksheet.write(self.startrow+i+1, 0, i+1)
            for col_num, value in enumerate([column['view'] for column in self.columns]):
                worksheet.write(self.startrow, col_num + 1, value, self.formats['header_format'])

            self.write_subtitles(worksheet, self.get_subtitles())
            self.endrow = self.startrow+len(df.index)
            for row in range(self.startrow, self.endrow):
                worksheet.conditional_format(
                    self.startrow,
                    0,
                    self.endrow,
                    len(df.columns),
                    {'type': 'cell',
                     'criteria': 'not equal to',
                     'value': -100,
                     'format': self.formats['normal_format']}
                )
            self.write_summary(worksheet)
            writer.save()

        elif self.format == 'csv':
            df.to_csv(
                path,
                header=[column['view'] for column in self.columns],
                index=False
            )

        link = '{}{}{}.{}'.format(
            'https://',
            self.link,
            self.file_name,
            self.format
        )
        return link, '.'.join([self.file_name, self.format])

    def write_subtitles(self, worksheet, subtitles):
        raise NotImplementedError('method is not implemented')

    def write_summary(self, worksheet):
        raise NotImplementedError('method is not implemented')

    def get_queryset(self):
        return get_operations(
            self.user,
            self.params
        )

    def parse_dataframe(self, df):
        raise NotImplementedError('method is not implemented')

    def get_title(self, params):
        raise NotImplementedError('method is not implemented')

    def get_dataframe(self):
        df = pd.DataFrame.from_records(self.get_queryset())
        return self.parse_dataframe(df)

    def get_subtitles(self):
        raise NotImplementedError('method is not implemented')

    def get_file_name(self):
        return 'Report'

    def add_formats(self, workbook):
        return {
            'title_format': workbook.add_format(self.style_settings['title']),
            'header_format': workbook.add_format(self.style_settings['header']),
            'subtitle_format': workbook.add_format(self.style_settings['subtitle']),
            'client_format': workbook.add_format(self.style_settings['client']),
            'normal_format': workbook.add_format(self.style_settings['normal']),
            'summary_text_format': workbook.add_format(self.style_settings['summary_text']),
            'summary_data_format': workbook.add_format(self.style_settings['summary_data'])
        }


class ClientJourneyReportManager(ReportManager):

    def __init__(self, user, params, **kwargs):
        super().__init__(user, params, **kwargs)

        self.columns = [
            {
                'name': 'date',
                'width': 12,
                'view': 'Дата'
            },
            {
                'name': 'time',
                'width': 10,
                'view': 'Время'
            },
            {
                'name': 'license_plate',
                'width': 13,
                'view': 'ГРЗ'
            },
            {
                'name': 'payment_mean',
                'width': 17,
                'view': 'RFID-метка'
            },
            {
                'name': 'vehicle_class',
                'width': 4,
                'view': 'ТГ'
            },
            {
                'name': 'point',
                'width': 8,
                'view': 'Место'
            },
            {
                'name': 'lane',
                'width': 8,
                'view': 'Полоса'
            },
            {
                'name': 'sum',
                'width': 10,
                'view': 'Сумма, руб. с НДС'
            },
            {
                'name': 'note',
                'width': 15,
                'view': 'Примечание'
            },
        ]

        self.client = Organization.objects.filter(
            pk=kwargs.get('client_id')
        ).first()
        self.contract = self.client.main_contract
        self.title_params = {
            'contract_number': self.contract.number,
            'contract_date': self.contract.created_date.date()
        }
        self.startrow = 9

    def get_queryset(self):
        return get_operations(
            self.user,
            self.params
        )

    def get_dataframe(self):
        qs = []

        for item in self.get_queryset():
            time_in = parse_datetime(timezone_converter(item['journeydetail__time_in']))
            parse_item = {
                'date': time_in[0],
                'time': time_in[1],
                'license_plate': item['license_plate'],
                'payment_mean': item['payment_mean'],
                'vehicle_class': item['vehicle_class'],
                'point': item['journeydetail__lane_in__point__name'],
                'lane': item['journeydetail__lane_in__number'],
                'sum': Decimal(item['sum']),
                'note': ''
            }
            qs.append(parse_item)
            if int(item['tariff_zone']) == 3:
                time_out = parse_datetime(timezone_converter(item['journeydetail__time_out']))
                new_item = {
                    'date': time_out[0],
                    'time': time_out[1],
                    'license_plate': item['license_plate'],
                    'payment_mean': item['payment_mean'],
                    'vehicle_class': item['vehicle_class'],
                    'point': item['journeydetail__lane_out__point__name'],
                    'lane': item['journeydetail__lane_out__number'],
                    'sum': Decimal('0.00'),
                    'note': 'транзит'
                }
                qs.append(new_item)
        df = pd.DataFrame.from_dict(qs)
        if not df.empty:
            self.total_amount = df['sum'].sum()
        else:
            self.total_amount = 0

        return df

    def parse_dataframe(self, df):
        if not df.empty:
            return df

    def get_title(self, params):
        return 'Ведомость проездов по договору № {contract_number} от {contract_date}'.format(**params)

    def get_subtitles(self):
        subtitles = {
            'current_date': get_local_current_date_string(),
            'date_from': get_date_string(self.date_from),
            'date_to':  get_date_string(self.date_to)
        }
        if self.client:
            subtitles['client'] = self.client.client_name

        return subtitles

    def write_subtitles(self, worksheet, subtitles):
        worksheet.merge_range(
            0, 0, 0, len(self.columns),
            self.get_title(params=self.title_params),
            self.formats['title_format']
        )

        worksheet.write(2, len(self.columns)-1, subtitles['current_date'], self.formats['subtitle_format'])
        if subtitles.get('client'):
            worksheet.merge_range(
                4, 0, 4, len(self.columns),
                subtitles['client'],
                self.formats['client_format']
            )
        worksheet.write(6, 1, 'Начало периода: ', self.formats['subtitle_format'])
        worksheet.write(6, 3, str(subtitles['date_from']), self.formats['subtitle_format'])
        worksheet.write(7, 1, 'Конец периода: ', self.formats['subtitle_format'])
        worksheet.write(7, 3, str(subtitles['date_to'])[:-7], self.formats['subtitle_format'])

    def write_summary(self, worksheet):
        worksheet.merge_range(
            self.endrow+2, 0, self.endrow+2, len(self.columns),
            'Сводные данные',
            self.formats['client_format']
        )

        worksheet.merge_range(
            self.endrow + 4, 0, self.endrow + 4, 3,
            'Остаток на начало периода',
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 6, 0, self.endrow + 6, 3,
            'Сумма проездов за период',
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 8, 0, self.endrow + 8, 3,
            'Остаток на конец периода',
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 4, 6, self.endrow + 4, 8,
            'Сумма поступлений за период',
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 6, 6, self.endrow + 6, 8,
            'Прочие операции за период',
            self.formats['summary_text_format']
        )

        worksheet.write(
            self.endrow + 4,
            4,
            self.client.get_balance_on_datetime(
                dt=datetime.strptime(self.date_from, '%Y-%m-%d')
            ), self.formats['summary_data_format'])
        worksheet.write(self.endrow + 6, 4, self.total_amount, self.formats['summary_data_format'])
        worksheet.write(
            self.endrow + 8,
            4,
            self.client.get_balance_on_datetime(
                dt=datetime.strptime(self.date_from, '%Y-%m-%d')
            ), self.formats['summary_data_format'])
        worksheet.write(self.endrow + 4, 9, self.get_positive_operations_sum(), self.formats['summary_data_format'])
        worksheet.write(self.endrow + 6, 9, self.get_negative_operations_sum(), self.formats['summary_data_format'])

        worksheet.merge_range(
            self.endrow + 10, 0, self.endrow + 10, 2,
            'Телефон',
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 10, 3, self.endrow + 10, 4,
            self.user.phone,
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 10, 5, self.endrow + 10, 7,
            'E-mail',
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 10, 8, self.endrow + 10, 9,
            self.user.email,
            self.formats['summary_text_format']
        )

    def get_positive_operations_sum(self):
        amount = Transaction.objects.filter(
            operation__created__range=[self.date_from, self.date_to],
            operation__client_id=self.client.id,
            status=TransactionStatus.SUCCESS,
            amount__gt=0
        ).aggregate(total_amount=Sum('amount')).get('total_amount', ' 0.00')
        if amount:
            return amount
        return Decimal('0.00')

    def get_negative_operations_sum(self):
        amount = Transaction.objects.exclude(
            operation__operation_type=OperationType.JOURNEY
        ).filter(
            operation__created__range=[self.date_from, self.date_to],
            operation__client_id=self.client.id,
            status=TransactionStatus.SUCCESS,
            amount__lt=0
        ).aggregate(total_amount=Sum('amount')).get('total_amount')
        if amount:
            return amount
        return Decimal('0.00')


class JourneyReportManager(ReportManager):

    def __init__(self, user, params, **kwargs):
        super().__init__(user, params, **kwargs)
        self.table_fields = ['sum', 'tariff_zone', 'payment_mean', 'vehicle_class',
                             'license_plate', 'journeydetail__lane_in__point__name',
                             'journeydetail__lane_in__number', 'journeydetail__lane_out__point__name',
                             'journeydetail__lane_out__number', 'journeydetail__time_in', 'journeydetail__time_out']

        self.columns = [
            {
                'name': 'date',
                'width': 12,
                'view': 'Дата'
            },
            {
                'name': 'time',
                'width': 10,
                'view': 'Время'
            },
            {
                'name': 'client_name',
                'width': 40,
                'view': 'Клиент'
            },
            {
                'name': 'license_plate',
                'width': 13,
                'view': 'ГРЗ'
            },
            {
                'name': 'payment_mean',
                'width': 17,
                'view': 'RFID-метка'
            },
            {
                'name': 'vehicle_class',
                'width': 4,
                'view': 'ТГ'
            },
            {
                'name': 'point',
                'width': 8,
                'view': 'Место'
            },
            {
                'name': 'lane',
                'width': 8,
                'view': 'Полоса'
            },
            {
                'name': 'sum',
                'width': 10,
                'view': 'Сумма, руб. с НДС'
            },
            {
                'name': 'note',
                'width': 15,
                'view': 'Примечание'
            },
        ]

        self.startrow = 9

    def get_queryset(self):
        return get_operations(
            self.user,
            self.params
        )

    def get_dataframe(self):
        qs = []

        for item in self.get_queryset():
            time_in = parse_datetime(timezone_converter(item['journeydetail__time_in']))
            parse_item = {
                'date': time_in[0],
                'time': time_in[1],
                'license_plate': item['license_plate'],
                'payment_mean': item['payment_mean'],
                'vehicle_class': item['vehicle_class'],
                'point': item['journeydetail__lane_in__point__name'],
                'lane': item['journeydetail__lane_in__number'],
                'sum': Decimal(item['sum']),
                'note': ''
            }
            qs.append(parse_item)
            if int(item['tariff_zone']) == 3:
                time_out = parse_datetime(timezone_converter(item['journeydetail__time_out']))
                new_item = {
                    'date': time_out[0],
                    'time': time_out[1],
                    'license_plate': item['license_plate'],
                    'payment_mean': item['payment_mean'],
                    'vehicle_class': item['vehicle_class_in'],
                    'point': item['journeydetail__lane_out__point__name'],
                    'lane': item['journeydetail__lane_out__number'],
                    'sum': Decimal('0.00'),
                    'note': 'транзит'
                }
                qs.append(new_item)
        df = pd.DataFrame.from_dict(qs)
        if not df.empty:
            self.total_amount = df['sum'].sum()
        else:
            self.total_amount = 0

        return df

    def parse_dataframe(self, df):
        if not df.empty:
            return df

    def get_title(self, params):
        return 'Ведомость проездов по договору № {contract_number} от {contract_date}'.format(**params)

    def get_subtitles(self):
        subtitles = {
            'current_date': get_local_current_date_string(),
            'date_from': get_date_string(self.date_from),
            'date_to':  get_date_string(self.date_to)
        }
        if self.client:
            subtitles['client'] = self.client.client_name

        return subtitles

    def write_subtitles(self, worksheet, subtitles):
        worksheet.merge_range(
            0, 0, 0, len(self.columns),
            self.get_title(params=self.title_params),
            self.formats['title_format']
        )

        worksheet.write(2, len(self.columns)-1, subtitles['current_date'], self.formats['subtitle_format'])
        if subtitles.get('client'):
            worksheet.merge_range(
                4, 0, 4, len(self.columns),
                subtitles['client'],
                self.formats['client_format']
            )
        worksheet.write(6, 1, 'Начало периода: ', self.formats['subtitle_format'])
        worksheet.write(6, 3, str(subtitles['date_from']), self.formats['subtitle_format'])
        worksheet.write(7, 1, 'Конец периода: ', self.formats['subtitle_format'])
        worksheet.write(7, 3, str(subtitles['date_to'])[:-7], self.formats['subtitle_format'])

    def write_summary(self, worksheet):
        worksheet.merge_range(
            self.endrow+2, 0, self.endrow+2, len(self.columns),
            'Сводные данные',
            self.formats['client_format']
        )

        worksheet.merge_range(
            self.endrow + 4, 0, self.endrow + 4, 3,
            'Остаток на начало периода',
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 6, 0, self.endrow + 6, 3,
            'Сумма проездов за период',
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 8, 0, self.endrow + 8, 3,
            'Остаток на конец периода',
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 4, 6, self.endrow + 4, 8,
            'Сумма поступлений за период',
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 6, 6, self.endrow + 6, 8,
            'Прочие операции за период',
            self.formats['summary_text_format']
        )

        worksheet.write(self.endrow + 4, 4, self.client.get_balance_on_datetime(dt=self.date_from), self.formats['summary_data_format'])
        worksheet.write(self.endrow + 6, 4, self.total_amount, self.formats['summary_data_format'])
        worksheet.write(self.endrow + 8, 4, self.client.get_balance_on_datetime(dt=self.date_to), self.formats['summary_data_format'])
        worksheet.write(self.endrow + 4, 9, self.get_positive_operations_sum(), self.formats['summary_data_format'])
        worksheet.write(self.endrow + 6, 9, self.get_negative_operations_sum(), self.formats['summary_data_format'])

        worksheet.merge_range(
            self.endrow + 10, 0, self.endrow + 10, 2,
            'Телефон',
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 10, 3, self.endrow + 10, 4,
            self.user.phone,
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 10, 5, self.endrow + 10, 7,
            'E-mail',
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 10, 8, self.endrow + 10, 9,
            self.user.email,
            self.formats['summary_text_format']
        )

    def get_positive_operations_sum(self):
        amount = Transaction.objects.filter(
            operation__created__range=[self.date_from, self.date_to],
            operation__client_id=self.client.id,
            status=TransactionStatus.SUCCESS,
            amount__gt=0
        ).aggregate(total_amount=Sum('amount')).get('total_amount', ' 0.00')
        if amount:
            return amount
        return Decimal('0.00')

    def get_negative_operations_sum(self):
        amount = Transaction.objects.exclude(
            operation__operation_type=OperationType.JOURNEY
        ).filter(
            operation__created__range=[self.date_from, self.date_to],
            operation__client_id=self.client.id,
            status=TransactionStatus.SUCCESS,
            amount__lt=0
        ).aggregate(total_amount=Sum('amount')).get('total_amount')
        if amount:
            return amount
        return Decimal('0.00')


class OperationReportManager(ReportManager):

    def __init__(self, user, params, **kwargs):
        super().__init__(user, params, **kwargs)
        self.columns = [
            {
                'name': 'operation_type',
                'width': 22,
                'view': 'Тип операции'
            },
            {
                'name': 'created_date',
                'width': 20,
                'view': 'Дата'
            },
            {
                'name': 'org_type',
                'width': 5,
                'view': 'Тип'
            },
            {
                'name': 'client_name',
                'width': 40,
                'view': 'Пользователь'
            },
            {
                'name': 'contract_number',
                'width': 10,
                'view': 'Договор'
            },
            {
                'name': 'license_plate',
                'width': 13,
                'view': 'ГРЗ'
            },
            {
                'name': 'vehicle_class',
                'width': 6,
                'view': 'Класс'
            },
            {
                'name': 'payment_mean',
                'width': 17,
                'view': 'Метка'
            },
            {
                'name': 'location',
                'width': 8,
                'view': 'Место'
            },
            {
                'name': 'sum',
                'width': 10,
                'view': 'Сумма'
            },
            {
                'name': 'status',
                'width': 10,
                'view': 'Статус'
            }
        ]

        self.startrow = 0
        self.params = params

    def get_queryset(self):
        return get_operations(
            self.user,
            self.params
        )

    def get_dataframe(self):
        qs = []
        for op in self.get_queryset():
            parse_item = {
                    'translation_type': OperationType.translations[op[1]],
                    'created_date': format_datetime(timezone_converter(op[4])),
                    'client_type': OrganizationType.translations.get(op[12]),
                    'client_name': op[11],
                    'contract_number': op[19],
                    'license_plate': op[9],
                    'vehicle_class': op[7],
                    'payment_mean': op[8],
                    'location': op[18],
                    'sum': op[5],
                    'status': OperationStatus.translations.get(op[3])
                }
            qs.append(parse_item)

        df = pd.DataFrame.from_dict(qs)
        return df

    def parse_dataframe(self, df):
        if not df.empty:
            return df

    def get_title(self, params):
        pass

    def get_subtitles(self):
        pass

    def write_subtitles(self, worksheet, subtitles):
        pass

    def write_summary(self, worksheet):
        pass


class ClientOperationReportManager(OperationReportManager):

    def __init__(self, user, params, **kwargs):
        super().__init__(user, params, **kwargs)
        self.table_fields = ['operation_type', 'created', 'license_plate', 'vehicle_class', 'payment_mean',
                             'journeydetail__lane_in__name', 'sum']

        self.columns = [
            {
                'name': 'operation_type',
                'width': 14,
                'view': 'Тип операции'
            },
            {
                'name': 'created_date',
                'width': 20,
                'view': 'Дата'
            },
            {
                'name': 'license_plate',
                'width': 12,
                'view': 'ГРЗ'
            },
            {
                'name': 'vehicle_class',
                'width': 6,
                'view': 'Класс'
            },
            {
                'name': 'payment_mean',
                'width': 17,
                'view': 'Метка'
            },
            {
                'name': 'name',
                'width': 20,
                'view': 'Наименование'
            },
            {
                'name': 'car',
                'width': 20,
                'view': 'Автомобиль'
            },
            {
                'name': 'location',
                'width': 8,
                'view': 'Место'
            },
            {
                'name': 'sum',
                'width': 10,
                'view': 'Сумма'
            }
        ]

        self.client = Organization.objects.filter(
            pk=kwargs.get('client_id')
        ).first()
        self.startrow = 0
        self.params = params

    def get_dataframe(self):
        qs = []
        for op in self.get_queryset():
            parse_item = {
                'translation_type': OperationType.translations[op[1]],
                'created_date': format_datetime(timezone_converter(op[4])),
                'license_plate': op[9],
                'vehicle_class': op[7],
                'payment_mean': op[8],
                'name': op[23],
                'car': op[26],
                'location': op[18],
                'sum': op[5],

            }
            qs.append(parse_item)

        df = pd.DataFrame.from_dict(qs)
        return df


class SingleClientReportManager(ReportManager):

    def __init__(self, user, params, **kwargs):
        self.client = Organization.objects.filter(
            pk=params.get('client')
        ).first()
        self.contract = self.client.main_contract

        super().__init__(user, params, **kwargs)

        self.columns = [
            {
                'name': 'operation_type',
                'width': 22,
                'view': 'Тип операции'
            },
            {
                'name': 'date',
                'width': 12,
                'view': 'Дата'
            },
            {
                'name': 'time',
                'width': 10,
                'view': 'Время'
            },
            {
                'name': 'license_plate',
                'width': 13,
                'view': 'ГРЗ'
            },
            {
                'name': 'payment_mean',
                'width': 17,
                'view': 'RFID-метка'
            },
            {
                'name': 'vehicle_class',
                'width': 4,
                'view': 'ТГ'
            },
            {
                'name': 'location',
                'width': 8,
                'view': 'Место'
            },
            {
                'name': 'sum',
                'width': 15,
                'view': 'Сумма, руб. с НДС'
            },
            {
                'name': 'note',
                'width': 15,
                'view': 'Примечание'
            },
        ]

        self.title_params = {
            'contract_number': self.contract.number,
            'contract_date': self.contract.created_date.date()
        }
        self.startrow = 9

    def get_file_name(self):
        file_name = self.contract.number

        return file_name

    def get_dataframe(self):
        qs = []
        self.journeys_amount = 0
        self.positive_amount = 0
        self.negative_amount = 0
        for op in self.get_queryset():
            if op[31]:
                time_in = parse_datetime(timezone_converter(op[31]))
            else:
                time_in = parse_datetime(timezone_converter(op[4]))
            parse_item = {
                'translation_type': OperationType.translations[op[1]],
                'date': time_in[0],
                'time': time_in[1],
                'license_plate': op[9],
                'payment_mean': op[8],
                'vehicle_class': op[7],
                'location': op[18],
                'sum': op[5],
                'note': ''
            }
            qs.append(parse_item)
            sum = op[5]
            if op[1] == OperationType.JOURNEY:
                self.journeys_amount += sum
            else:
                if sum < 0:
                    self.negative_amount += sum
                else:
                    self.positive_amount += sum

            if op[1] == OperationType.JOURNEY and int(op[6]) == 3:
                # В случае поездки по третьей зоне добавляем строчку с нулевой ценой
                time_out = parse_datetime(timezone_converter(op[32]))
                new_item = {
                    'date': time_out[0],
                    'time': time_out[1],
                    'license_plate': op[9],
                    'payment_mean': op[8],
                    'vehicle_class': op[30],
                    'location': op[33],
                    'sum': Decimal('0.00'),
                    'note': 'транзит'
                }
                qs.append(new_item)
        df = pd.DataFrame.from_dict(qs)
        return df

    def get_title(self, params):
        return 'Ведомость проездов  и операций по договору № {contract_number} от {contract_date}'.format(**params)

    def get_subtitles(self):
        subtitles = {
            'current_date': get_local_current_date_string(),
            'date_from': get_date_string(self.date_from),
            'date_to':  get_date_string(self.date_to)
        }
        if self.client:
            subtitles['client'] = self.client.client_name

        return subtitles

    def write_subtitles(self, worksheet, subtitles):
        worksheet.merge_range(
            0, 0, 0, len(self.columns),
            self.get_title(params=self.title_params),
            self.formats['title_format']
        )

        worksheet.write(2, len(self.columns)-1, subtitles['current_date'], self.formats['subtitle_format'])
        if subtitles.get('client'):
            worksheet.merge_range(
                4, 0, 4, len(self.columns),
                subtitles['client'],
                self.formats['client_format']
            )
        worksheet.write(6, 1, 'Начало периода: ', self.formats['subtitle_format'])
        worksheet.write(6, 3, str(subtitles['date_from']), self.formats['subtitle_format'])
        worksheet.write(7, 1, 'Конец периода: ', self.formats['subtitle_format'])
        worksheet.write(7, 3, str(subtitles['date_to']), self.formats['subtitle_format'])

    def write_summary(self, worksheet):
        worksheet.merge_range(
            self.endrow+2, 0, self.endrow+2, len(self.columns),
            'Сводные данные',
            self.formats['client_format']
        )

        worksheet.merge_range(
            self.endrow + 4, 0, self.endrow + 4, 3,
            'Остаток на начало периода',
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 6, 0, self.endrow + 6, 3,
            'Сумма проездов за период',
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 8, 0, self.endrow + 8, 3,
            'Остаток на конец периода',
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 4, 6, self.endrow + 4, 8,
            'Сумма поступлений за период',
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 6, 6, self.endrow + 6, 8,
            'Прочие операции за период',
            self.formats['summary_text_format']
        )

        worksheet.write(
            self.endrow + 4,
            4,
            'В разработке',    # self.client.get_balances_on_date(dt=datetime.strptime(self.date_from, '%Y-%m-%d').date())[0],
            self.formats['summary_data_format'])
        worksheet.write(self.endrow + 6, 4, self.journeys_amount, self.formats['summary_data_format'])
        worksheet.write(
            self.endrow + 8,
            4,
            'В разработке',    # self.client.get_balances_on_date(dt=datetime.strptime(self.date_to, '%Y-%m-%d').date())[1],
            self.formats['summary_data_format'])
        worksheet.write(self.endrow + 4, 9, self.positive_amount, self.formats['summary_data_format'])
        worksheet.write(self.endrow + 6, 9, self.negative_amount, self.formats['summary_data_format'])

        worksheet.merge_range(
            self.endrow + 10, 0, self.endrow + 10, 2,
            'Телефон',
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 10, 3, self.endrow + 10, 4,
            self.user.phone,
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 10, 5, self.endrow + 10, 7,
            'E-mail',
            self.formats['summary_text_format']
        )
        worksheet.merge_range(
            self.endrow + 10, 8, self.endrow + 10, 9,
            self.user.email,
            self.formats['summary_text_format']
        )

    def get_positive_operations_sum(self):
        # Пока не используются, будут нужны для сверки отчета
        amount = Transaction.objects.filter(
            operation__created__range=[self.date_from, self.date_to],
            operation__client_id=self.client.id,
            status=TransactionStatus.SUCCESS,
            amount__gt=0
        ).aggregate(total_amount=Sum('amount')).get('total_amount', ' 0.00')
        if amount:
            return amount
        return Decimal('0.00')

    def get_negative_operations_sum(self):
        # Пока не используются, будут нужны для сверки отчета
        amount = Transaction.objects.exclude(
            operation__operation_type=OperationType.JOURNEY
        ).filter(
            operation__created__range=[self.date_from, self.date_to],
            operation__client_id=self.client.id,
            status=TransactionStatus.SUCCESS,
            amount__lt=0
        ).aggregate(total_amount=Sum('amount')).get('total_amount')
        if amount:
            return amount
        return Decimal('0.00')


class DefaultReportManager:

    def __init__(self, user, **kwargs):
        self.datetime_string = get_local_current_datetime_string()
        self.user = user
        self.date_from = '2021-06-01'
        self.date_to = '2021-07-01'
        self.path = settings.MEDIA_ROOT
        self.dir = 'archive_reports/' + self.datetime_string + '/'
        self.file_name = 'Report_' + self.datetime_string
        self.root_dir = self.path + self.dir
        os.makedirs(self.path + '/reports/', exist_ok=True)
        self.base_name = self.path + 'reports/' + self.file_name
        self.link = '{}{}{}.{}'.format(
            'https://',
            ''.join([settings.DOMAIN, settings.MEDIA_URL]),
            'reports/' + self.file_name,
            'zip'
        )

    def get_period_operations(self, client):
        operations = Operation.objects.filter(
            created__range=[self.date_from, self.date_to],
            client_id=client.id
        ).all()
        if len(operations) > 0:
            return True

        return False

    def generate(self):
        from tickets.tasks import generate_archive
        generate_archive(
            user_id=self.user.id,
            base_name=self.base_name,
            root_dir=self.root_dir
        )
        return self.link, self.file_name


class ClientsReportManager(ReportManager):

    def __init__(self, user, params, **kwargs):
        super().__init__(user, params, **kwargs)
        self.columns = [
            {
                'name': 'client',
                'width': 60,
                'view': 'Клиент'
            },
            {
                'name': 'org_type',
                'width': 5,
                'view': 'Тип'
            },
            {
                'name': 'inn',
                'width': 20,
                'view': 'ИНН'
            },
            {
                'name': 'contract_number',
                'width': 10,
                'view': '№ договора'
            },
            {
                'name': 'contract_date',
                'width': 20,
                'view': 'Дата договора'
            },
            {
                'name': 'status',
                'width': 15,
                'view': 'Статус'
            }
        ]

        self.startrow = 0
        self.params = params

    def get_file_name(self):
        return 'Clients_{}'.format(get_local_current_date_string('%d_%m_%Y'))

    def get_queryset(self):
        return get_clients(
            self.user,
            self.params
        )

    def get_dataframe(self):
        qs = []
        for item in self.get_queryset():
            parse_item = {
                    'client': item['client'],
                    'org_type': OrganizationType.translations.get(item['org_type']),
                    'inn': item['inn'],
                    'contract_number': item['contract_number'],
                    'contract_date': datetime.strptime(
                        item['contract_date'], "%Y-%m-%dT%H:%M:%SZ"
                    ).strftime("%d.%m.%Y"),
                    'status': ContractStatus.translations.get(item['status'])
                }
            qs.append(parse_item)

        df = pd.DataFrame.from_dict(qs)
        return df

    def get_title(self, params):
        pass

    def get_subtitles(self):
        pass

    def write_subtitles(self, worksheet, subtitles):
        pass

    def write_summary(self, worksheet):
        pass


class LabelsReportManager(ReportManager):
    def __init__(self, user, params, **kwargs):
        super().__init__(user, params, **kwargs)
        self.columns = [
            {
                'name': 'pan',
                'width': 20,
                'view': 'PAN'
            },
            {
                'name': 'enabled_date',
                'width': 20,
                'view': 'Дата выдачи'
            },
            {
                'name': 'client',
                'width': 60,
                'view': 'Клиент'
            },
            {
                'name': 'contract_number',
                'width': 20,
                'view': 'Договор'
            },
            {
                'name': 'license_plate',
                'width': 10,
                'view': 'ГРЗ'
            },
            {
                'name': 'name',
                'width': 20,
                'view': 'Наименование'
            },
            {
                'name': 'car',
                'width': 20,
                'view': 'Автомобиль'
            },
            {
                'name': 'vehicle_class',
                'width': 6,
                'view': 'Класс'
            },
            {
                'name': 'status',
                'width': 15,
                'view': 'Статус'
            }
        ]

        self.startrow = 0
        self.params = params

    def get_file_name(self):
        return 'Labels_{}'.format(get_local_current_date_string('%d_%m_%Y'))

    def get_queryset(self):
        return get_labels(
            self.user,
            self.params
        )

    def get_dataframe(self):
        qs = []
        for item in self.get_queryset():
            enabled_date = datetime.strptime(
                        item['enabled_date'], "%Y-%m-%dT%H:%M:%S"
                    ).strftime("%Y-%m-%d %H:%M:%S") if item['enabled_date'] else ''
            parse_item = {
                    'pan': item['pan'],
                    'enabled_date': enabled_date,
                    'client': item['client_name'],
                    'contract_number': item['contract_number'],
                    'license_plate': item['license_plate'],
                    'name': item['name'],
                    'car': item['car'],
                    'tariff_group': item['tariff_group'],
                    'status': LabelStatus.translations.get(item['status'])
                }
            qs.append(parse_item)

        df = pd.DataFrame.from_dict(qs)
        return df

    def get_title(self, params):
        pass

    def get_subtitles(self):
        pass

    def write_subtitles(self, worksheet, subtitles):
        pass

    def write_summary(self, worksheet):
        pass
'''
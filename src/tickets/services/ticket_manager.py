import io
import json
import qrcode
import base64
import zstd

from datetime import timedelta

from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA512
from Crypto.PublicKey import RSA

from tickets.models import *
from tickets.services.setting_manager import SettingManager
from tickets.models import TicketType


class TicketManager:
    def __init__(self, **kwargs):
        self.sm = SettingManager()
        self.seller = kwargs.get('seller')
        self.token = kwargs.get('token')
        self.key_path = settings.KEY_PATH
        self.private_key_filename = settings.PRIVATE_KEY_FILENAME
        self.public_key_filename = settings.PUBLIC_KEY_FILENAME
        self.algorithm = 'V01'

    def generate_qr(self, ticket):
        raise NotImplementedError('method is not implemented')

    def get_ticket_cost(self):
        raise NotImplementedError('method is not implemented')

    def get_start_date(self):
        raise NotImplementedError('method is not implemented')

    def get_end_date(self):
        raise NotImplementedError('method is not implemented')

    def create_ticket(self, seller_id, **kwargs):
        raise NotImplementedError('method is not implemented')

    def make_ticket_data(self, **kwargs):
        raise NotImplementedError('method is not implemented')

    def canonical_message(self, data):
        return '_'.join([
            data[0],
            data[2],
            data[3],
            data[4],
            data[5]
        ])

    def sign(self, message):
        key = RSA.import_key(open('/'.join([
            self.key_path,
            self.private_key_filename
        ])).read())
        h = SHA512.new(message.encode('utf-8'))
        signature = pkcs1_15.new(key).sign(h)

        return base64.b64encode(signature).decode('utf-8')

    def verify(self, data, is_compressed=False):
        if is_compressed:
            data = zstd.decompress(data).decode('utf-8')
        data = json.loads(data)
        message = self.canonical_message(data)
        key = RSA.import_key(open('/'.join([
            self.key_path,
            self.public_key_filename
        ])).read())
        h = SHA512.new(message.encode('utf-8'))
        signature = base64.b64decode(data[-1])
        try:
            pkcs1_15.new(key).verify(h, signature)
            return True
        except (ValueError, TypeError):
            return False

    def hash_json(self, json_string):
        h = hashlib.sha256()
        h.update(json_string.encode('utf-8'))
        return h.hexdigest()


class SingleTicketManager(TicketManager):
    def __init__(self, **kwargs):
        self.ticket_type_number = TicketType.SINGLE
        self.ticket_type = TicketType.objects.get(number=self.ticket_type_number)
        super().__init__(**kwargs)

    def get_qr_data(self, ticket, is_compressed=False):
        """
        Добавляет информацию о билете в json
        """
        ticket_info = [
            str(ticket.id),
            str(self.ticket_type.code),
            ticket.series,
            str(ticket.number.id).zfill(8),
            ticket.start_date.strftime('%d.%m.%Y'),
            ticket.end_date.strftime('%d.%m.%Y'),
            self.algorithm,
            self.ticket_type.get_repr_vehicle_type_numbers()
        ]
        message = self.canonical_message(ticket_info)
        ticket_info.append(self.sign(message))
        if is_compressed:
            return self.compress_zstd(ticket_info)
        return json.dumps(ticket_info)

    def make_ticket_data(self, **kwargs):
        ticket = Ticket.objects.filter(
            token=self.token
        ).first()
        if not ticket:
            ticket = self.create_ticket(**kwargs)
        data = {
            'ticket_name': self.ticket_type.name,
            'series': ticket.series,
            'number': str(ticket.number.id).zfill(8),
            'company_name': self.sm.ticket_main_company,
            'agent_name': ticket.agent_name,
            'vehicle_type': self.ticket_type.get_repr_vehicle_types(),
            'created_date': ticket.created.strftime('%d.%m.%Y'),
            'start_date': ticket.start_date.strftime('%d.%m.%Y'),
            'end_date': ticket.end_date.strftime('%d.%m.%Y'),
            'ticket_zone': self.ticket_type.zone.name,
            'amount': ticket.amount,
            'qr_code': bytes(ticket.qr_code)
        }

        return data

    def compress_zstd(self, data):
        # Convert to JSON
        json_data = json.dumps(data)
        # Convert to bytes
        encoded = json_data.encode('utf-8')
        # Compress
        compressed = zstd.compress(encoded)
        return compressed

    def generate_qr(self, ticket):
        qr = qrcode.QRCode(
            version=None,
            error_correction=self.sm.qr_error_correction,
            box_size=self.sm.qr_box_size,
            border=self.sm.qr_border,
        )
        qr.add_data(self.get_qr_data(ticket))
        qr.make(fit=True)

        img = qr.make_image(fill_color=self.sm.qr_color, back_color=self.sm.qr_back_color)

        # TODO Временное решение для тестирования и показа QR кодов.
        # Изображение доступно по адресу api/uploads/codes/{uuid}.png
        img.save('/'.join([settings.QR_PATH, '{}.png']).format(ticket.id), format="PNG")

        in_mem_file = io.BytesIO()

        img.save(in_mem_file, format="PNG")
        # reset file pointer to start
        in_mem_file.seek(0)
        img_bytes = in_mem_file.read()
        return base64.b64encode(img_bytes)

    def generate_test_qr(self, ticket, ticket_info):
        qr = qrcode.QRCode(
            version=None,
            error_correction=self.sm.qr_error_correction,
            box_size=self.sm.qr_box_size,
            border=self.sm.qr_border,
        )
        qr.add_data(ticket_info)
        qr.make(fit=True)

        img = qr.make_image(fill_color=self.sm.qr_color, back_color=self.sm.qr_back_color)

        # TODO Временное решение для тестирования и показа QR кодов.
        # Изображение доступно по адресу api/uploads/codes/{uuid}.png
        img.save('/'.join([settings.QR_PATH, '{}.png']).format(ticket.id), format="PNG")

        in_mem_file = io.BytesIO()

        img.save(in_mem_file, format="PNG")
        # reset file pointer to start
        in_mem_file.seek(0)
        img_bytes = in_mem_file.read()
        return base64.b64encode(img_bytes)

    def create_ticket(self, **kwargs):
        with transaction.atomic():
            ticket = Ticket.objects.create(
                token=self.token,
                series=self.generate_series(),
                seller_id=self.seller.id,
                ticket_type_id=self.ticket_type.id,
                amount=self.get_ticket_cost(),
                start_date=self.get_start_date(),
                end_date=self.get_end_date()
            )
            TicketNumber.objects.create(
                ticket_id=ticket.id
            )

            qr_code = self.generate_qr(ticket)

            ticket.qr_code = qr_code
            ticket.save()

        return ticket

    def generate_series(self):
        return '-'.join([datetime.now().strftime('%y%m'), self.ticket_type.code])

    def get_start_date(self):
        return datetime.now().date()

    def get_end_date(self):
        return (datetime.now() + timedelta(days=int(self.ticket_type.lifetime))).date()

    def get_ticket_cost(self):
        return float(self.ticket_type.tariff.cost)



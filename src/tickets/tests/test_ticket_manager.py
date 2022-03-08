import csv
import json

from rest_framework.test import APIClient

from tickets.tests.parent_data import ParentTestDataMixin
from tickets.services.ticket_manager import SingleTicketManager
from tickets.common.actions import create_seller, create_test_tickets
from tickets.models import *


class TicketManagerTests(ParentTestDataMixin):
    def setUp(self):
        super().setUp()

        company = Company.objects.get(inn='7800000000')
        seller = create_seller(
            company=company,
            user_dict={'code': 1000},
            password='test_password'
        )
        self.tm = SingleTicketManager(
            seller=seller,
            token='token'
        )

    def test_sign(self):
        ticket = self.tm.create_ticket()
        data = self.tm.get_qr_data(ticket)
        success = self.tm.verify(data)
        self.assertEqual(success, True)

    def test_create_test_tickets(self):
        pass




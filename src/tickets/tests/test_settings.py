from tickets.tests.parent_data import ParentTestDataMixin
from tickets.models import Setting, TicketType
from tickets.services.setting_manager import SettingManager


class SettingsTests(ParentTestDataMixin):

    def setUp(self):
        super().setUp()

    def test_setting_manager(self):
        sm = SettingManager()
        sm.clear()
        sm.refresh_from_db()


class CompanyCategory:
    MAIN = 0
    AGENT = 1
    CARRIER = 2

    choices = (
        (MAIN, 'Организатор перевозок'),
        (AGENT, 'Агент'),
        (CARRIER, 'Перевозчик'),
    )


class UserRole:
    ADMIN = 0
    SECURITY_ADMIN = 1
    AGENT = 2
    SELLER = 3
    CARRIER = 4
    INSPECTOR = 5
    VALIDATOR = 6
    REPORT_MANAGER = 7
    PASSENGER = 8

    choices = (
        (ADMIN, 'Администратор'),
        (SECURITY_ADMIN, 'Администратор ИБ'),
        (AGENT, 'Агент'),
        (SELLER, 'Продавец'),
        (CARRIER, 'Перевозчик'),
        (INSPECTOR, 'Контроллер'),
        (VALIDATOR, 'Стационарный валидатор'),
        (REPORT_MANAGER, 'Аналитик'),
        (PASSENGER, 'Пассажир')
    )


class OperationType:
    TRIP = 0

    choices = (
        (TRIP, 'Поездка'),
    )


class RevenueType:
    NOT_DISTRIBUTED = 0
    COMPENSATION = 1

    choices = (
        (NOT_DISTRIBUTED, 'Выручка не распределяется'),
        (COMPENSATION, 'Возмещение '),
    )


class TariffType:
    CONSTANT = 0
    MUTABLE = 1

    choices = (
        (CONSTANT, 'Нерегулируемый'),
        (MUTABLE, 'Регулируемый'),
    )


class RouteType:
    MUNICIPAL = 0
    INTERMUNICIPAL = 1
    INTERREGIONAL = 2

    choices = (
        (MUNICIPAL, 'Муниципальный'),
        (INTERMUNICIPAL, 'Межмуниципальный'),
        (INTERREGIONAL, 'Смежный межрегиональный'),
    )


class DeviceType:
    SALE = 0
    MAKE_TRIP = 1
    CONTROL = 2

    choices = (
        (SALE, 'Продажа'),
        (MAKE_TRIP, 'Гашение'),
        (CONTROL, 'Контроль')
    )

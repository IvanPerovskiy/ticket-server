class UserStatus:
    NEW = 0
    ACTIVE = 1
    BLOCKED = 2
    DELETED = 3

    choices = (
        (NEW, 'Новый'),
        (ACTIVE, 'Активный'),
        (BLOCKED, 'Заблокированный'),
        (DELETED, 'Удаленный'),
    )


class CompanyStatus:
    NEW = 0
    ACTIVE = 1
    BLOCKED = 2
    DELETED = 3

    choices = (
        (NEW, 'Новый'),
        (ACTIVE, 'Активный'),
        (BLOCKED, 'Заблокированный'),
        (DELETED, 'Удаленный'),
    )


class DeviceStatus:
    ACTIVE = 1
    BLOCKED = 2

    choices = (
        (ACTIVE, 'Активный'),
        (BLOCKED, 'Заблокированный')
    )


class TariffStatus:
    ACTIVE = 1
    BLOCKED = 2
    DISABLED = 3

    choices = (
        (ACTIVE, 'Активный'),
        (BLOCKED, 'Заблокированный'),
        (DISABLED, 'Отключенный'),
    )


class WorkdayStatus:
    OPEN = 1
    CLOSED = 2

    choices = (
        (OPEN, 'Открыта'),
        (CLOSED, 'Закрыта')
    )


class TicketTypeStatus:
    ACTIVE = 1
    BLOCKED = 2
    DISABLED = 3

    choices = (
        (ACTIVE, 'Активный'),
        (BLOCKED, 'Заблокированный'),
        (DISABLED, 'Отключенный'),
    )


class TicketStatus:
    ACTIVE = 1
    COMPLETED = 2
    DISABLED = 3

    choices = (
        (ACTIVE, 'Активный'),
        (COMPLETED, 'Завершенный'),
        (DISABLED, 'Списанный'),
    )

    check_statuses = {
        'ACTIVE': {
            'code': 600,
            'detail': 'Билет не погашен'
        },
        'COMPLETED': {
            'code': 601,
            'detail': 'Билет погашен'
        },
        'COMPLETED_HERE': {
            'code': 602,
            'detail': 'Билет погашен ранее на этом рейсе'
        },
        'COMPLETED_NOT_HERE': {
            'code': 603,
            'detail': 'Билет погашен не на этом рейсе'
        },
        'EXPIRED': {
            'code': 604,
            'detail': 'Билет просрочен'
        },
        'DISABLED': {
            'code': 605,
            'detail': 'Билет не валиден'
        },
        'NOT_FOUND': {
            'code': 606,
            'detail': 'Билет не найден'
        }
    }


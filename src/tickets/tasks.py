from celery import shared_task


@shared_task
def task_every_day():
    """
    Запускается каждые 00:00 по московскому времени
    Действия:
    """
    pass


@shared_task
def task_every_month():
    """
    Запускается каждые 00:00 в первый день месяца по московскому времени
    """
    pass


@shared_task
def task_every_year():
    """
    Запускается каждые 00:00 1 января по московскому времени
    Действия:
    """
    pass


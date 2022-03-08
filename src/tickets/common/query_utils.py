"""
Created on 24.08.2021

:author: Ivan Perovsky
Функции для обработки запросов из БД
"""
import logging

logger = logging.getLogger(__name__)


def trim_query(qs, limit=None, offset=0):
    offset = int(offset)
    limit = len(qs) if not limit else int(limit) + offset

    return qs[offset: limit]


def orderby_query(items, orderby):
    try:
        return sorted(
            items,
            key=lambda i: (
                i[orderby.replace('-', '')] is None, i[orderby.replace('-', '')]
            ), reverse=orderby.startswith('-')
        )
    except Exception as e:
        logger.error('ERROR orderby_query {}'.format(e))

    return items

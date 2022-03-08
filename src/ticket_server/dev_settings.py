from .settings import *

DEBUG = True

DOMAIN = os.environ.get('BSTR_DOMAIN', 'qr.mybstr.com')
##
# bstr
#
DATABASES['default']['PASSWORD'] = 'ticket'
DATABASES['default']['HOST'] = 'ticket_dev_db'

##
# email
#
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_PORT = None

# -- Admin settings ---
ADMIN_USER = 'admin@admin.ru'
ADMIN_PASSWORD = 'uB4hD3'

# -- Superuser settings ---
SUPERUSER_NAME = 'superbstradmin'
SUPERUSER_PASSWORD = 'uB4hD3'

SIMPLE_JWT = {
    'SLIDING_TOKEN_LIFETIME': timedelta(weeks=1),
    'ACCESS_TOKEN_LIFETIME': timedelta(weeks=1)
}


# -- SENTRY ----------------
sentry_sdk.init(
    dsn="https://8255d3e13c5847b08a2baae44ffd4dad@o401913.ingest.sentry.io/6020806",
    integrations=[DjangoIntegration()],

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True
)



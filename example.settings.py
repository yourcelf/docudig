from default_settings import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'docudig',
        'USER': 'docudig',
        'PASSWORD': 'docudig',
        'HOST': '',
        'PORT': '',
    }
}

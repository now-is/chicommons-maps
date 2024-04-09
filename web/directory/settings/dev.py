from .base import *
import os

DEBUG=True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / '/data/db.sqlite3',
    }
}
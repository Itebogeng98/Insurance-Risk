import os

from .settings import *  # noqa: F403

DEBUG = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False') == 'True'
SECURE_HSTS_PRELOAD = os.environ.get('SECURE_HSTS_PRELOAD', 'False') == 'True'
# The supplied proxy overwrites this header and is the only exposed service.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = [origin for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if origin]
REQUIRE_VALIDATED_MODEL = True
MODEL_MIN_ACCURACY = 0.85
MODEL_MIN_MACRO_F1 = 0.80
MEDIA_ROOT = Path(os.environ.get('MEDIA_ROOT', '/data/media'))
MODEL_DIR = Path(os.environ.get('MODEL_DIR', '/data/models'))
STATIC_ROOT = Path('/data/static')

"""Render web-only deployment; training requires separate durable infrastructure."""

from .production import *  # noqa: F403

hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '').strip()
if hostname:
    ALLOWED_HOSTS = [*ALLOWED_HOSTS, hostname]
    CSRF_TRUSTED_ORIGINS = [*CSRF_TRUSTED_ORIGINS, f'https://{hostname}']

DATABASES['default']['CONN_MAX_AGE'] = 60
DATABASES['default']['CONN_HEALTH_CHECKS'] = True
DATABASES['default']['OPTIONS'] = {'sslmode': 'require', 'connect_timeout': 10}

MIDDLEWARE = list(MIDDLEWARE)
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

# Never accept durable jobs/files into Render's ephemeral web filesystem.
TRAINING_ENABLED = False
MODEL_ACTIVATION_ENABLED = False
MEDIA_ROOT = BASE_DIR / 'media'
MODEL_DIR = BASE_DIR / 'risk_engine' / 'ml_models'
SECURE_REDIRECT_EXEMPT = [r'^healthz/$']

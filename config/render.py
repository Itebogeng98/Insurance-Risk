"""Render deployment with optional disk-backed, supervised training."""

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

# Startup verifies the mount before starting either process. Off by default so
# existing free services do not silently accept files into ephemeral storage.
TRAINING_ENABLED = os.environ.get('RENDER_TRAINING_ENABLED', 'False') == 'True'
MODEL_ACTIVATION_ENABLED = TRAINING_ENABLED
RENDER_DATA_ROOT = Path('/var/data')
MEDIA_ROOT = RENDER_DATA_ROOT / 'media' if TRAINING_ENABLED else BASE_DIR / 'media'
MODEL_DIR = RENDER_DATA_ROOT / 'models' if TRAINING_ENABLED else BASE_DIR / 'risk_engine' / 'ml_models'
SECURE_REDIRECT_EXEMPT = [r'^healthz/$']

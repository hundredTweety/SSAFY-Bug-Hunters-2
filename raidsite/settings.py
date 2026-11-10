import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.getenv('DJANGO_DEBUG', '0' if os.getenv('RENDER_EXTERNAL_HOSTNAME') else '1') == '1'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'local-development-only-key-not-for-production')
if not DEBUG and (not os.getenv('DJANGO_SECRET_KEY') or len(SECRET_KEY) < 40):
    raise ImproperlyConfigured('Production needs a DJANGO_SECRET_KEY of at least 40 characters.')
render_hostname = os.getenv('RENDER_EXTERNAL_HOSTNAME','').strip()
ALLOWED_HOSTS = [x.strip() for x in os.getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',') if x.strip()]
CSRF_TRUSTED_ORIGINS = [x.strip() for x in os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if x.strip()]
# Render supplies the actual public host; don't guess an onrender.com domain.
if render_hostname:
    if render_hostname not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(render_hostname)
    if f'https://{render_hostname}' not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(f'https://{render_hostname}')
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'raid',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'raidsite.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [], 'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]
WSGI_APPLICATION = 'raidsite.wsgi.application'
ASGI_APPLICATION = 'raidsite.asgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
if os.getenv('DATABASE_URL'):
    import dj_database_url
    DATABASES['default'] = dj_database_url.parse(
        os.environ['DATABASE_URL'],
        conn_max_age=0,  # A serverless Neon database can sleep between requests.
        conn_health_checks=True,
        ssl_require=not DEBUG,  # TLS for external production PostgreSQL.
    )
elif not DEBUG:
    raise ImproperlyConfigured('DATABASE_URL is mandatory in production; SQLite is not persistent on free hosts.')
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'}}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 60
SESSION_SAVE_EVERY_REQUEST = False  # Persist only modified auth sessions; anonymous demo uses a separate signed cookie.
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 3600 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
X_FRAME_OPTIONS = 'DENY'
RAID_INVITE_CODE = os.getenv('RAID_INVITE_CODE','').strip()
if not DEBUG and not RAID_INVITE_CODE:
    raise ImproperlyConfigured('Configure RAID_INVITE_CODE for the private class event.')
RAID_MAX_HP = max(1, int(os.getenv('RAID_MAX_HP','1000')))
RAID_DAMAGE = max(1, int(os.getenv('RAID_DAMAGE','20')))
RAID_MAX_CLEARS_PER_PLAYER = max(1, int(os.getenv('RAID_MAX_CLEARS_PER_PLAYER','3')))
RAID_RESULTS_PUBLIC = os.getenv('RAID_RESULTS_PUBLIC','0') == '1'

# Portfolio mode: do not create live players/attempts/clears or modify boss HP.
RAID_DEMO_MODE = os.getenv('RAID_DEMO_MODE', '0') == '1'

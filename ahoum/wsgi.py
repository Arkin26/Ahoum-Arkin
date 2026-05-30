import os

from django.core.wsgi import get_wsgi_application

if os.environ.get("VERCEL"):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ahoum.settings.production")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ahoum.settings.local")

application = get_wsgi_application()
app = application

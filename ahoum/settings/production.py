from .base import *  # noqa: F403

DEBUG = False

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Celery has no worker on Vercel — run tasks inline so enroll confirmations still log.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Upstash / other managed Redis over TLS
redis_url = env("REDIS_URL", default="")
if redis_url.startswith("rediss://"):
    CACHES["default"]["OPTIONS"]["CONNECTION_POOL_KWARGS"] = {"ssl_cert_reqs": None}  # noqa: F405

if not ALLOWED_HOSTS:  # noqa: F405
    ALLOWED_HOSTS = [".vercel.app"]

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405

import logging
import random

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


def generate_otp():
    return f"{random.randint(0, 999999):06d}"


def send_otp_email(email, otp):
    logger.info(
        "EMAIL OTP for %s: %s (expires in %s seconds)",
        email,
        otp,
        settings.OTP_TTL_SECONDS,
    )


def store_otp(email, otp):
    cache.set(f"otp:{email}", otp, timeout=settings.OTP_TTL_SECONDS)
    cache.set(f"otp_attempts:{email}", 0, timeout=settings.OTP_TTL_SECONDS)


def verify_otp(email, otp):
    attempts = cache.get(f"otp_attempts:{email}", 0)
    if attempts >= settings.OTP_MAX_ATTEMPTS:
        return False, "max_attempts"

    stored = cache.get(f"otp:{email}")
    if not stored:
        return False, "expired"

    if stored != otp.strip():
        cache.set(f"otp_attempts:{email}", attempts + 1, timeout=settings.OTP_TTL_SECONDS)
        return False, "invalid"

    cache.delete(f"otp:{email}")
    cache.delete(f"otp_attempts:{email}")
    return True, "ok"

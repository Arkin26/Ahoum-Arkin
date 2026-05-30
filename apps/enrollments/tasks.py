import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def send_enrollment_confirmation(enrollment_id):
    from .models import Enrollment

    try:
        enrollment = Enrollment.objects.select_related("event", "seeker").get(pk=enrollment_id)
    except Enrollment.DoesNotExist:
        return

    logger.info(
        "ENROLLMENT CONFIRMATION | seeker=%s | event='%s' | starts=%s",
        enrollment.seeker.email,
        enrollment.event.title,
        enrollment.event.starts_at.isoformat(),
    )


@shared_task
def send_followup_email(enrollment_id):
    from .models import Enrollment

    try:
        enrollment = Enrollment.objects.select_related("event", "seeker").get(pk=enrollment_id)
    except Enrollment.DoesNotExist:
        return

    if enrollment.status != Enrollment.STATUS_ENROLLED:
        return

    logger.info(
        "FOLLOW-UP EMAIL (1hr after enroll) | seeker=%s | event='%s'",
        enrollment.seeker.email,
        enrollment.event.title,
    )


@shared_task
def send_event_reminder(enrollment_id):
    from .models import Enrollment

    try:
        enrollment = Enrollment.objects.select_related("event", "seeker").get(pk=enrollment_id)
    except Enrollment.DoesNotExist:
        return

    if enrollment.status != Enrollment.STATUS_ENROLLED:
        return

    logger.info(
        "EVENT REMINDER (1hr before start) | seeker=%s | event='%s' | starts=%s",
        enrollment.seeker.email,
        enrollment.event.title,
        enrollment.event.starts_at.isoformat(),
    )


def schedule_enrollment_emails(enrollment):
    enrollment_id = str(enrollment.id)

    # Serverless (Vercel): no Celery worker or broker scheduling — log confirmation only.
    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
        send_enrollment_confirmation(enrollment_id)
        return

    send_enrollment_confirmation.delay(enrollment_id)
    send_followup_email.apply_async(args=[enrollment_id], countdown=3600)

    reminder_at = enrollment.event.starts_at - timedelta(hours=1)
    if reminder_at > timezone.now():
        send_event_reminder.apply_async(args=[enrollment_id], eta=reminder_at)

"""
jobs/emails.py — Centralised email sending helpers.

How Django email works:
1. Django's `send_mail()` / `EmailMultiAlternatives` build the message.
2. They hand it off to whatever EMAIL_BACKEND is configured in settings.
3. In development we use `console.EmailBackend` → printed to the terminal.
4. In production we swap to `smtp.EmailBackend` and point at a real SMTP
    server (Gmail, SendGrid, Mailgun, etc.) via the EMAIL_* env vars.

    send_mail(subject, plain_body, from_email, [recipient_list])
                                ↓
                        EMAIL_BACKEND (console / SMTP)
                                ↓
                            Recipient inbox
"""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def _send(subject: str, template: str, context: dict, to: list[str]) -> None:
    """
    Internal helper that renders an HTML template, strips it to a plain-text
    fallback, then sends a multipart/alternative email.

    EmailMultiAlternatives lets us attach *both* the HTML version and the
    plain-text fallback — mail clients that can't render HTML see the text.
    """
    html_body = render_to_string(template, context)
    text_body = strip_tags(html_body)          # safe plain-text fallback

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to,
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=True)  # never crash the request on email failure


# ── Public API ────────────────────────────────────────────────────────────────

def send_registration_confirmation(user) -> None:
    """
    Sent to a new user immediately after successful registration.
    Confirms their account is active and encourages them to browse jobs.
    """
    _send(
        subject="Welcome to JobBoard — you're all set! 🎉",
        template="emails/registration_confirmation.html",
        context={"user": user},
        to=[user.email],
    )


def send_application_confirmation(application) -> None:
    """
    Sent to the job seeker when they submit an application.
    Reassures them that their application was received and what happens next.
    """
    _send(
        subject=f"Application received — {application.job.title}",
        template="emails/application_confirmation.html",
        context={"application": application},
        to=[application.applicant.email],
    )


def send_employer_notification(application) -> None:
    """
    Sent to the employer (company owner) when a new application arrives.
    Drives them back to the platform to review it.
    """
    employer_email = application.job.company.owner.email
    if not employer_email:
        return
    _send(
        subject=f'New application for "{application.job.title}"',
        template="emails/employer_notification.html",
        context={"application": application},
        to=[employer_email],
    )

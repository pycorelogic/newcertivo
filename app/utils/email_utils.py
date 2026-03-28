import logging
from typing import Optional

from flask import current_app, render_template_string

logger = logging.getLogger(__name__)

# ─── Email Templates ─────────────────────────────────────────────────────────

_CONTACT_NOTIFICATION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: Arial, sans-serif; color: #1e293b; background: #f8fafc; margin: 0; padding: 20px; }
    .card { background: #ffffff; border-radius: 8px; padding: 32px; max-width: 600px; margin: 0 auto;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .header { border-bottom: 3px solid #2563eb; padding-bottom: 16px; margin-bottom: 24px; }
    .header h2 { margin: 0; color: #2563eb; font-size: 20px; }
    .field { margin-bottom: 16px; }
    .label { font-size: 12px; font-weight: 700; text-transform: uppercase; color: #64748b;
             letter-spacing: 0.05em; margin-bottom: 4px; }
    .value { font-size: 15px; color: #1e293b; background: #f8fafc; padding: 10px 14px;
             border-radius: 4px; border-left: 3px solid #2563eb; }
    .message-body { white-space: pre-wrap; }
    .footer { margin-top: 24px; padding-top: 16px; border-top: 1px solid #e2e8f0;
              font-size: 12px; color: #94a3b8; text-align: center; }
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h2>📬 New Contact Message — {{ site_name }}</h2>
    </div>
    <div class="field">
      <div class="label">From</div>
      <div class="value">{{ name }} &lt;{{ email }}&gt;</div>
    </div>
    <div class="field">
      <div class="label">Subject</div>
      <div class="value">{{ subject }}</div>
    </div>
    <div class="field">
      <div class="label">Message</div>
      <div class="value message-body">{{ message }}</div>
    </div>
    <div class="footer">
      This message was submitted via the contact form on {{ site_name }}.
    </div>
  </div>
</body>
</html>
"""

_COMMENT_NOTIFICATION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: Arial, sans-serif; color: #1e293b; background: #f8fafc; margin: 0; padding: 20px; }
    .card { background: #ffffff; border-radius: 8px; padding: 32px; max-width: 600px; margin: 0 auto;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .header { border-bottom: 3px solid #7c3aed; padding-bottom: 16px; margin-bottom: 24px; }
    .header h2 { margin: 0; color: #7c3aed; font-size: 20px; }
    .field { margin-bottom: 16px; }
    .label { font-size: 12px; font-weight: 700; text-transform: uppercase; color: #64748b;
             letter-spacing: 0.05em; margin-bottom: 4px; }
    .value { font-size: 15px; color: #1e293b; background: #f8fafc; padding: 10px 14px;
             border-radius: 4px; border-left: 3px solid #7c3aed; }
    .btn { display: inline-block; margin-top: 20px; padding: 12px 24px; background: #7c3aed;
           color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 700; font-size: 14px; }
    .footer { margin-top: 24px; padding-top: 16px; border-top: 1px solid #e2e8f0;
              font-size: 12px; color: #94a3b8; text-align: center; }
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h2>💬 New Comment Awaiting Moderation</h2>
    </div>
    <div class="field">
      <div class="label">Post</div>
      <div class="value">{{ post_title }}</div>
    </div>
    <div class="field">
      <div class="label">Commenter</div>
      <div class="value">{{ commenter_name }} &lt;{{ commenter_email }}&gt;</div>
    </div>
    {% if is_reply %}
    <div class="field">
      <div class="label">In Reply To</div>
      <div class="value">{{ parent_author }}</div>
    </div>
    {% endif %}
    <div class="field">
      <div class="label">Comment</div>
      <div class="value">{{ comment_content }}</div>
    </div>
    <a href="{{ admin_url }}" class="btn">Review in Admin Panel →</a>
    <div class="footer">
      Submitted on {{ site_name }}. Please review and approve or reject this comment.
    </div>
  </div>
</body>
</html>
"""

_CONTACT_AUTO_REPLY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: Arial, sans-serif; color: #1e293b; background: #f8fafc; margin: 0; padding: 20px; }
    .card { background: #ffffff; border-radius: 8px; padding: 32px; max-width: 600px; margin: 0 auto;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .header { background: linear-gradient(135deg, #2563eb, #7c3aed); border-radius: 6px 6px 0 0;
              padding: 24px 32px; margin: -32px -32px 24px; }
    .header h1 { margin: 0; color: #ffffff; font-size: 22px; }
    .header p  { margin: 6px 0 0; color: rgba(255,255,255,0.85); font-size: 14px; }
    p { line-height: 1.7; color: #475569; }
    .highlight { background: #eff6ff; border-left: 4px solid #2563eb; padding: 12px 16px;
                 border-radius: 0 4px 4px 0; margin: 20px 0; font-style: italic; color: #1e40af; }
    .footer { margin-top: 24px; padding-top: 16px; border-top: 1px solid #e2e8f0;
              font-size: 12px; color: #94a3b8; text-align: center; }
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h1>{{ site_name }}</h1>
      <p>Thank you for reaching out!</p>
    </div>
    <p>Hi <strong>{{ name }}</strong>,</p>
    <p>
      We've received your message and one of our team members will get back to you
      as soon as possible — usually within 1–2 business days.
    </p>
    <div class="highlight">
      <strong>Your subject:</strong> {{ subject }}
    </div>
    <p>
      In the meantime, feel free to explore our latest articles on the blog.
      We publish new content regularly covering technology, business, lifestyle and more.
    </p>
    <p>Thanks again for writing in!</p>
    <p>Warm regards,<br><strong>The {{ site_name }} Team</strong></p>
    <div class="footer">
      You are receiving this email because you submitted the contact form on {{ site_name }}.
      Please do not reply directly to this email.
    </div>
  </div>
</body>
</html>
"""


# ─── Sender Helpers ──────────────────────────────────────────────────────────

def _get_mail():
    """Lazily import the mail extension to avoid circular imports."""
    from app.extensions import mail
    return mail


def _send(subject: str, recipients: list[str], html_body: str,
          sender: Optional[str] = None) -> bool:
    """
    Low-level send helper.

    Returns True on success, False on failure (logs the error).
    Never raises so that form submissions are not blocked by mail errors.
    """
    from flask_mail import Message

    if not recipients:
        logger.warning("email_utils._send called with no recipients — skipping.")
        return False

    effective_sender = sender or current_app.config.get(
        "MAIL_DEFAULT_SENDER", "noreply@certivo.com"
    )

    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=html_body,
            sender=effective_sender,
        )
        _get_mail().send(msg)
        logger.info("Email sent: subject=%r recipients=%r", subject, recipients)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Failed to send email subject=%r to %r: %s",
            subject, recipients, exc, exc_info=True,
        )
        return False


# ─── Public API ──────────────────────────────────────────────────────────────

def send_contact_notification(
    name: str,
    email: str,
    subject: str,
    message: str,
) -> bool:
    """
    Notify the site admin that a new contact-form message has arrived.
    Also sends an auto-reply acknowledgement to the sender.
    """
    site_name = current_app.config.get("SITE_NAME", "Certivo")
    admin_email = current_app.config.get("ADMIN_EMAIL", "admin@certivo.com")

    # ── Admin notification ──────────────────────────────────────────────────
    admin_html = render_template_string(
        _CONTACT_NOTIFICATION_TEMPLATE,
        site_name=site_name,
        name=name,
        email=email,
        subject=subject,
        message=message,
    )
    _send(
        subject=f"[{site_name}] New Contact: {subject}",
        recipients=[admin_email],
        html_body=admin_html,
    )

    # ── Auto-reply to sender ────────────────────────────────────────────────
    reply_html = render_template_string(
        _CONTACT_AUTO_REPLY_TEMPLATE,
        site_name=site_name,
        name=name,
        subject=subject,
    )
    return _send(
        subject=f"We received your message — {site_name}",
        recipients=[email],
        html_body=reply_html,
    )


def send_comment_notification(
    post_title: str,
    post_slug: str,
    commenter_name: str,
    commenter_email: str,
    comment_content: str,
    is_reply: bool = False,
    parent_author: Optional[str] = None,
) -> bool:
    """
    Notify the admin that a new comment is awaiting moderation.
    """
    site_name = current_app.config.get("SITE_NAME", "Certivo")
    site_url = current_app.config.get("SITE_URL", "http://localhost:5000")
    admin_email = current_app.config.get("ADMIN_EMAIL", "admin@certivo.com")
    admin_url = f"{site_url}/admin/comments"

    html_body = render_template_string(
        _COMMENT_NOTIFICATION_TEMPLATE,
        site_name=site_name,
        post_title=post_title,
        commenter_name=commenter_name,
        commenter_email=commenter_email,
        comment_content=comment_content,
        is_reply=is_reply,
        parent_author=parent_author or "",
        admin_url=admin_url,
    )

    return _send(
        subject=f"[{site_name}] New comment on '{post_title}'",
        recipients=[admin_email],
        html_body=html_body,
    )


def send_generic_email(
    subject: str,
    recipients: list[str],
    html_body: str,
    sender: Optional[str] = None,
) -> bool:
    """Generic helper exposed for use in other parts of the application."""
    return _send(subject=subject, recipients=recipients,
                 html_body=html_body, sender=sender)

import json
import logging
import smtplib
import urllib.error
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)

SMTP_TIMEOUT = settings.SMTP_TIMEOUT_SECONDS
RESEND_API_URL = "https://api.resend.com/emails"

RESET_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0A0A15;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:40px 20px;">
        <table width="520" cellpadding="0" cellspacing="0" style="background:#13132A;border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,0.06);">
          <tr>
            <td style="padding:40px 36px 8px;text-align:center;">
              <span style="font-size:22px;font-weight:800;color:#fff;letter-spacing:0.08em;">MONITORING</span>
              <span style="font-size:12px;font-weight:600;color:rgba(255,255,255,0.5);letter-spacing:0.18em;display:block;margin-top:2px;">INNOVATION</span>
            </td>
          </tr>
          <tr>
            <td style="padding:28px 36px 12px;">
              <h2 style="color:#fff;font-size:20px;margin:0 0 8px;">Recuperación de contraseña</h2>
              <p style="color:rgba(255,255,255,0.7);font-size:14px;line-height:1.6;margin:0;">
                Recibimos una solicitud para restablecer la contraseña de tu cuenta.
                Haz clic en el botón de abajo para crear una nueva contraseña.
              </p>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:16px 36px;">
              <a href="%s"
                 style="display:inline-block;padding:14px 36px;background:linear-gradient(135deg,#7B5BFF,#C6007E);color:#fff;text-decoration:none;border-radius:10px;font-size:15px;font-weight:700;letter-spacing:0.03em;">
                Restablecer contraseña
              </a>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 36px 32px;">
              <p style="color:rgba(255,255,255,0.4);font-size:12px;line-height:1.5;margin:0;text-align:center;">
                Si no solicitaste este cambio, ignora este correo.<br>
                El enlace expira en 10 minutos.
              </p>
            </td>
          </tr>
          <tr>
            <td style="background:rgba(255,255,255,0.02);padding:16px 36px;text-align:center;border-top:1px solid rgba(255,255,255,0.04);">
              <span style="color:rgba(255,255,255,0.25);font-size:11px;">
                Monitoring Innovation &bull; Todos los derechos reservados
              </span>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

NOTIFICATION_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0A0A15;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:40px 20px;">
        <table width="520" cellpadding="0" cellspacing="0" style="background:#13132A;border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,0.06);">
          <tr>
            <td style="padding:40px 36px 8px;text-align:center;">
              <span style="font-size:22px;font-weight:800;color:#fff;letter-spacing:0.08em;">MONITORING</span>
              <span style="font-size:12px;font-weight:600;color:rgba(255,255,255,0.5);letter-spacing:0.18em;display:block;margin-top:2px;">INNOVATION</span>
            </td>
          </tr>
          <tr>
            <td style="padding:28px 36px 12px;">
              <h2 style="color:#fff;font-size:20px;margin:0 0 8px;">Contraseña actualizada</h2>
              <p style="color:rgba(255,255,255,0.7);font-size:14px;line-height:1.6;margin:0;">
                La contraseña de tu cuenta en <strong>Monitoring Innovation</strong> ha sido cambiada exitosamente.
              </p>
              <p style="color:rgba(255,255,255,0.7);font-size:14px;line-height:1.6;margin:16px 0 0;">
                Si no realizaste este cambio, contacta al administrador de inmediato.
              </p>
            </td>
          </tr>
          <tr>
            <td style="background:rgba(255,255,255,0.02);padding:16px 36px;text-align:center;border-top:1px solid rgba(255,255,255,0.04);">
              <span style="color:rgba(255,255,255,0.25);font-size:11px;">
                Monitoring Innovation &bull; Todos los derechos reservados
              </span>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _from_header() -> str:
    name = settings.SMTP_FROM_NAME or settings.APP_NAME
    return f"{name} <{settings.email_from_address}>"


def _log_email_fallback(to_email: str, subject: str, reset_url: str | None = None) -> None:
    logger.warning("=" * 60)
    logger.warning("Email no configurado o falló — correo NO enviado:")
    logger.warning("  Para:     %s", to_email)
    logger.warning("  Asunto:   %s", subject)
    if reset_url:
        logger.warning("  Enlace:   %s", reset_url)
    logger.warning("=" * 60)
    if settings.DEBUG and reset_url:
        print(f"\n[EMAIL] Para: {to_email}\n[EMAIL] Enlace: {reset_url}\n")


def _send_via_resend(to_email: str, subject: str, html: str) -> None:
    payload = json.dumps(
        {
            "from": _from_header(),
            "to": [to_email],
            "subject": subject,
            "html": html,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        RESEND_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "MonitoringInnovation-API/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8", errors="replace")
        logger.info("Correo enviado (Resend) a %s: %s — %s", to_email, subject, body[:120])
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        logger.error("Resend HTTP %s: %s", exc.code, detail)
        raise
    except urllib.error.URLError as exc:
        logger.error("Resend no alcanzable: %s", exc.reason)
        raise


def _send_via_smtp(to_email: str, subject: str, html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = _from_header()
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    if settings.SMTP_PORT == 465:
        with smtplib.SMTP_SSL(
            settings.SMTP_HOST, settings.SMTP_PORT, timeout=SMTP_TIMEOUT
        ) as server:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
    else:
        with smtplib.SMTP(
            settings.SMTP_HOST, settings.SMTP_PORT, timeout=SMTP_TIMEOUT
        ) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())

    logger.info("Correo enviado (SMTP) a %s: %s", to_email, subject)


def _send_email(to_email: str, subject: str, html: str, *, reset_url: str | None = None) -> bool:
    if not settings.email_configured:
        _log_email_fallback(to_email, subject, reset_url)
        return False

    try:
        if settings.resend_configured:
            _send_via_resend(to_email, subject, html)
        else:
            _send_via_smtp(to_email, subject, html)
        return True
    except urllib.error.HTTPError:
        # Detalle ya registrado en _send_via_resend (p. ej. 403: solo email de prueba en Resend)
        _log_email_fallback(to_email, subject, reset_url)
        return False
    except OSError as exc:
        logger.error(
            "Red inalcanzable al enviar correo (%s). En Railway no uses Gmail SMTP; usa RESEND_API_KEY.",
            exc,
        )
        _log_email_fallback(to_email, subject, reset_url)
        return False
    except Exception:
        logger.exception("Error al enviar correo a %s: %s", to_email, subject)
        _log_email_fallback(to_email, subject, reset_url)
        return False


def build_reset_password_url(reset_token: str) -> str:
    base = settings.FRONTEND_URL.rstrip("/")
    return f"{base}/reset-password?token={reset_token}"


def send_reset_password_email(to_email: str, reset_token: str) -> None:
    reset_url = build_reset_password_url(reset_token)
    html = RESET_TEMPLATE % reset_url
    _send_email(
        to_email,
        "Recuperación de contraseña — Monitoring Innovation",
        html,
        reset_url=reset_url,
    )


def send_password_changed_notification(to_email: str) -> None:
    _send_email(to_email, "Contraseña actualizada — Monitoring Innovation", NOTIFICATION_TEMPLATE)

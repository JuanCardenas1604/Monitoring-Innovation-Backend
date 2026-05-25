import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)

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


def _smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USERNAME and settings.SMTP_PASSWORD)


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


def _send_email(to_email: str, subject: str, html: str) -> None:
    if not _smtp_configured():
        logger.info("=" * 60)
        logger.info("SMTP no configurado — correo no enviado:")
        logger.info("  Para:     %s", to_email)
        logger.info("  Asunto:   %s", subject)
        logger.info("=" * 60)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    from_name = settings.SMTP_FROM_NAME or settings.APP_NAME
    msg["From"] = f"{from_name} <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
        logger.info("Correo enviado a %s: %s", to_email, subject)
    except Exception:
        logger.exception("Error al enviar correo a %s: %s", to_email, subject)


def send_reset_password_email(to_email: str, reset_token: str) -> None:
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    html = RESET_TEMPLATE % reset_url

    if not _smtp_configured():
        logger.info("SMTP no configurado — el enlace se habría enviado a %s", to_email)
        print(f"\n[EMAIL] El enlace de recuperación fue enviado a {to_email}\n")
        return

    _send_email(to_email, "Recuperación de contraseña — Monitoring Innovation", html)


def send_password_changed_notification(to_email: str) -> None:
    _send_email(to_email, "Contraseña actualizada — Monitoring Innovation", NOTIFICATION_TEMPLATE)

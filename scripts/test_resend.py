"""
Prueba de envío con Resend (misma API que el backend en producción).

Uso (desde la carpeta backend):
    python scripts/test_resend.py
    python scripts/test_resend.py otro@email.com
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.services.email_service import _send_via_resend


def main() -> None:
    to = sys.argv[1] if len(sys.argv) > 1 else "juanchotv123@gmail.com"

    if not settings.resend_configured:
        print("ERROR: define RESEND_API_KEY en .env o en Railway")
        raise SystemExit(1)

    print(f"Enviando prueba a {to} desde {settings.email_from_address} ...")
    _send_via_resend(
        to,
        "Prueba Monitoring Innovation — Resend",
        "<p>Si ves esto, <strong>Resend funciona</strong> con tu backend.</p>",
    )
    print("OK — revisa la bandeja de entrada (y spam).")


if __name__ == "__main__":
    main()

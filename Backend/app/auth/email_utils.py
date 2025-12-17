# email_utils.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import json
import urllib.request
import socket

load_dotenv()

def send_email(destinatario: str, subject: str, body: str):
    remitente = os.getenv("EMAIL_USER")
    clave = os.getenv("EMAIL_PASSWORD")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    if not remitente or not clave:
        print("⚠️  EMAIL_USER/EMAIL_PASSWORD not set. Skipping email send.")
        return False

    msg = MIMEMultipart()
    msg["From"] = remitente
    msg["To"] = destinatario
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            if smtp_port == 587:
                server.starttls()
                server.ehlo()
            server.login(remitente, clave)
            server.sendmail(remitente, destinatario, msg.as_string())
        print("✅ Correo enviado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al enviar correo vía SMTP: {e}")

        # Si falla la conexión de red o SMTP, intentar fallback vía SendGrid API
        sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        if sendgrid_api_key:
            try:
                return send_via_sendgrid(destinatario, subject, body, remitente, sendgrid_api_key)
            except Exception as ex:
                print(f"❌ Fallback SendGrid falló: {ex}")
                return False

        return False


def send_via_sendgrid(destinatario: str, subject: str, body: str, remitente: str, api_key: str) -> bool:
    """Enviar correo usando la API HTTP de SendGrid (sin dependencias externas)."""
    url = "https://api.sendgrid.com/v3/mail/send"
    payload = {
        "personalizations": [{"to": [{"email": destinatario}], "subject": subject}],
        "from": {"email": remitente},
        "content": [{"type": "text/html", "value": body}]
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.getcode()
            if 200 <= status < 300:
                print("✅ Correo enviado vía SendGrid correctamente")
                return True
            else:
                print(f"❌ SendGrid respondió con status {status}")
                return False
    except urllib.error.HTTPError as he:
        body = he.read().decode(errors="ignore") if hasattr(he, 'read') else ''
        print(f"❌ Error HTTP SendGrid: {he.code} - {body}")
        return False
    except Exception as e:
        print(f"❌ Excepción al llamar SendGrid: {e}")
        return False

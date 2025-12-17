# email_utils.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

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
        print(f"❌ Error al enviar correo: {e}")
        return False

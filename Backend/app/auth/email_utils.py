# email_utils.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(destinatario: str, subject: str, body: str):
    remitente = "ssemicompany@gmail.com"
    clave = "vvum tamq hror lkoj"  # <-- ejemplo: sin espacios (pon aquí TU app password real sin espacios)

    msg = MIMEMultipart()
    msg["From"] = remitente
    msg["To"] = destinatario
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(remitente, clave)
            server.sendmail(remitente, destinatario, msg.as_string())
        print("✅ Correo enviado correctamente")
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")
        raise

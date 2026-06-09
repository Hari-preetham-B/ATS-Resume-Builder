# utils/mail_helper.py
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Brevo SMTP
SMTP_SERVER = "smtp-relay.brevo.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("BREVO_SMTP_USER")
SMTP_PASSWORD = os.getenv("BREVO_SMTP_PASSWORD")
FROM_EMAIL = "no-reply@brevo.com"
FROM_NAME = "ATS Resume Builder"
def send_email(to, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent to {to}")
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def send_otp_email(to, otp):
    subject = "Your OTP Code - ATS Resume Builder"
    body = f"""<div style="font-family: Arial; padding: 20px;">
        <h2>Your OTP Code</h2>
        <h1 style="color: #4df;">{otp}</h1>
        <p>This code expires in 5 minutes.</p>
    </div>"""
    return send_email(to, subject, body)

def send_reset_email(to, token):
    reset_link = f"http://localhost:5000/reset-password.html?token={token}"
    subject = "Password Reset Request - ATS Resume Builder"
    body = f"""<div style="font-family: Arial; padding: 20px;">
        <h2>Reset Your Password</h2>
        <p>Click the link below to set a new password:</p>
        <a href="{reset_link}" style="background: #4df; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a>
        <p>If you didn't request this, please ignore this email.</p>
        <hr>
        <p style="font-size: 12px;">ATS Resume Builder</p>
    </div>"""
    return send_email(to, subject, body)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "abhi23kk@gmail.com"
EMAIL_PASSWORD = "shaelevzwynztaib"   # no spaces

def send_email(to, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent to {to}")
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def send_otp_email(to, otp):
    subject = "Your OTP Code"
    body = f"""<div style="font-family: Arial; padding: 20px;">
        <h2>Your OTP Code</h2>
        <h1 style="color: #4df;">{otp}</h1>
        <p>This code expires in 5 minutes.</p>
    </div>"""
    return send_email(to, subject, body)

def send_reset_email(to, token):
    reset_link = f"http://localhost:5000/reset-password.html?token={token}"
    subject = "Password Reset Request"
    body = f"""<div style="font-family: Arial; padding: 20px;">
        <h2>Reset Your Password</h2>
        <p>Click the link below:</p>
        <a href="{reset_link}" style="background: #4df; color: white; padding: 10px 20px; text-decoration: none;">Reset Password</a>
        <p>If you didn't request this, ignore this email.</p>
    </div>"""
    return send_email(to, subject, body)
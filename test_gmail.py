"""
Script kiểm tra nhanh kết nối Gmail IMAP + SMTP
Chạy: python test_gmail.py
"""
import imaplib
import smtplib
import sys
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL    = os.getenv("GMAIL_ADDRESS", "")
PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

if not EMAIL or not PASSWORD:
    print("[FAIL] Chua co GMAIL_ADDRESS hoac GMAIL_APP_PASSWORD trong file .env")
    sys.exit(1)

print(f"Kiem tra ket noi cho: {EMAIL}")
print("-" * 40)

# ── Test IMAP ──────────────────────────────────────────────────────
print("[1/2] Kiem tra IMAP (doc email)...")
try:
    mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    mail.login(EMAIL, PASSWORD)
    status, data = mail.select("INBOX")
    count = int(data[0]) if data[0] else 0
    mail.logout()
    print(f"  OK! Ket noi IMAP thanh cong. Hop thu co {count} email.")
except imaplib.IMAP4.error as e:
    print(f"  FAIL! Loi IMAP: {e}")
    print()
    print("  Goi y:")
    print("  - Dung App Password (16 ky tu), khong phai mat khau Gmail")
    print("  - Bat IMAP: Gmail > Settings > Forwarding and POP/IMAP > Enable IMAP")
    print("  - Bat 2FA: myaccount.google.com/security")
    sys.exit(1)

# ── Test SMTP ──────────────────────────────────────────────────────
print("[2/2] Kiem tra SMTP (gui email)...")
try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.login(EMAIL, PASSWORD)
    print("  OK! Ket noi SMTP thanh cong. Co the gui email.")
except smtplib.SMTPAuthenticationError as e:
    print(f"  FAIL! Loi xac thuc SMTP: {e}")
    sys.exit(1)
except Exception as e:
    print(f"  FAIL! Loi SMTP: {e}")
    sys.exit(1)

print()
print("=" * 40)
print("Gmail da san sang! Co the chay ung dung.")
print("=" * 40)

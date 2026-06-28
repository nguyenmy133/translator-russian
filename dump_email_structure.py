import imaplib
import email
import sys
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("GMAIL_ADDRESS", "")
PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

print(f"Connecting to IMAP for: {EMAIL}")
try:
    mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    mail.login(EMAIL, PASSWORD)
    mail.select("INBOX")
    
    # Target UID 13087
    uid = b"13087"
    status, msg_data = mail.uid("fetch", uid, "(BODY.PEEK[])")
    if status != "OK" or not msg_data or not msg_data[0]:
        print(f"Failed to fetch UID {uid.decode()}")
        mail.logout()
        sys.exit(1)
        
    raw_bytes = msg_data[0][1] if isinstance(msg_data[0], tuple) else None
    if not raw_bytes:
        print("Empty raw bytes")
        mail.logout()
        sys.exit(1)
        
    msg = email.message_from_bytes(raw_bytes)
    print(f"Subject: {msg.get('Subject')}")
    print(f"From: {msg.get('From')}")
    print(f"Date: {msg.get('Date')}")
    print(f"Is Multipart: {msg.is_multipart()}")
    print("-" * 50)
    
    for i, part in enumerate(msg.walk()):
        content_type = part.get_content_type()
        content_disposition = part.get("Content-Disposition", "")
        filename = part.get_filename()
        print(f"Part {i+1}:")
        print(f"  Content-Type: {content_type}")
        print(f"  Content-Disposition: {content_disposition}")
        print(f"  Filename (get_filename()): {filename}")
        print(f"  Headers:")
        for name, value in part.items():
            print(f"    {name}: {value}")
        print("-" * 50)
        
    mail.logout()
except Exception as e:
    import traceback
    traceback.print_exc()

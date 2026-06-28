import imaplib
import email
import sys
import os
import re
import time
from email.header import decode_header
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("GMAIL_ADDRESS", "")
PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

def decode_str(s) -> str:
    if s is None:
        return ""
    parts = decode_header(s)
    result = ""
    for part, charset in parts:
        if isinstance(part, bytes):
            result += part.decode(charset or "utf-8", errors="replace")
        else:
            result += str(part)
    return result

print(f"Connecting to IMAP for: {EMAIL}")
try:
    mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    mail.login(EMAIL, PASSWORD)
    mail.select("INBOX")
    print("Connected successfully!")
    
    # Search unseen
    status, data = mail.uid("search", None, "UNSEEN")
    all_uids = data[0].split()
    print(f"Total unseen emails: {len(all_uids)}")
    
    uids_to_check = all_uids[-50:]
    if not uids_to_check:
        print("No unseen emails to check.")
        mail.logout()
        sys.exit(0)
        
    uid_csv = ",".join([uid.decode() for uid in uids_to_check])
    print(f"Bulk fetching UIDs: {uid_csv}")
    
    start_time = time.time()
    
    status, fetch_data = mail.uid("fetch", uid_csv, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT CONTENT-TYPE)])")
    if status != "OK":
        print(f"Fetch failed: {status}")
        mail.logout()
        sys.exit(1)
        
    print(f"Bulk fetch completed in {time.time() - start_time:.2f} seconds.")
    print(f"Number of items in response: {len(fetch_data)}")
    
    # Now let's parse them
    parsed_count = 0
    for item in fetch_data:
        if not isinstance(item, tuple):
            continue
            
        # item is a tuple: (envelope_info, header_bytes)
        envelope = item[0].decode(errors="replace")
        header_bytes = item[1]
        
        # Extract UID from envelope using regex
        # format is usually like: b'13087 (UID 13087 BODY[HEADER.FIELDS ...] {98}'
        uid_match = re.search(r"UID\s+(\d+)", envelope)
        if not uid_match:
            continue
            
        uid_str = uid_match.group(1)
        header_msg = email.message_from_bytes(header_bytes)
        
        subject = decode_str(header_msg.get("Subject", ""))
        sender = decode_str(header_msg.get("From", ""))
        content_type = header_msg.get("Content-Type", "")
        
        safe_subj = subject.encode('ascii', errors='replace').decode()
        safe_sender = sender.encode('ascii', errors='replace').decode()
        print(f"Parsed UID: {uid_str} | From: {safe_sender} | Subj: {safe_subj} | Content-Type: {content_type.strip()}")
        parsed_count += 1
        
    print(f"Successfully parsed {parsed_count} email headers.")
    mail.logout()
except Exception as e:
    import traceback
    traceback.print_exc()

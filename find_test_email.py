import imaplib
import email
import sys
import os
import re
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

def is_russian_docx(filename: str) -> bool:
    if not filename:
        return False
    name = filename.lower().strip()

    # Bỏ qua các file audio (chứa từ "audio")
    if "audio" in name:
        return False

    if not name.endswith(".docx"):
        return False
    # Pattern 1: kết thúc bằng " ru.docx" (space trước ru, không ngoặc) — format thực tế
    if re.search(r'\sru\.docx$', name):
        return True
    # Pattern 2: chứa "(ru)" ở bất kỳ đâu trong tên — format có ngoặc
    if re.search(r'\(ru\)', name):
        return True
    return False

print(f"Connecting to IMAP for: {EMAIL}")
try:
    mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    mail.login(EMAIL, PASSWORD)
    mail.select("INBOX")
    print("Connected successfully!")
    
    # Search all UNSEEN
    status, data = mail.uid("search", None, "UNSEEN")
    all_uids = data[0].split()
    print(f"Total unseen emails: {len(all_uids)}")
    
    # Check newest 50 unseen
    uids_to_check = all_uids[-50:]
    print("Checking newest 50 unseen emails (from newest to oldest)...")
    
    found_any = False
    for i, uid in enumerate(reversed(uids_to_check)):
        uid_str = uid.decode()
        status, header_data = mail.uid(
            "fetch", uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT CONTENT-TYPE DATE)])"
        )
        if status != "OK" or not header_data or not header_data[0]:
            continue
            
        raw_header = header_data[0][1] if isinstance(header_data[0], tuple) else b""
        header_msg = email.message_from_bytes(raw_header)
        subject = decode_str(header_msg.get("Subject", ""))
        sender = decode_str(header_msg.get("From", ""))
        date = decode_str(header_msg.get("Date", ""))
        content_type = header_msg.get("Content-Type", "")
        
        attachments = []
        is_multipart = "multipart" in content_type.lower()
        
        if is_multipart:
            status, msg_data = mail.uid("fetch", uid, "(BODY.PEEK[])")
            if status == "OK" and msg_data and msg_data[0]:
                raw_bytes = msg_data[0][1] if isinstance(msg_data[0], tuple) else None
                if raw_bytes:
                    msg = email.message_from_bytes(raw_bytes)
                    for part in msg.walk():
                        content_disposition = part.get("Content-Disposition", "")
                        # Note: We want to see all attachments first
                        filename = part.get_filename()
                        if filename:
                            filename_decoded = decode_str(filename)
                            # Log disposition too
                            attachments.append((filename_decoded, content_disposition))
                            
        # Print without emoji to avoid encoding crash
        # Filter non-ascii characters for terminal safety
        safe_subj = subject.encode('ascii', errors='replace').decode()
        safe_sender = sender.encode('ascii', errors='replace').decode()
        print(f"[{i+1}] UID: {uid_str} | From: {safe_sender} | Subj: {safe_subj} | Date: {date}")
        if attachments:
            for fname, disp in attachments:
                matched = is_russian_docx(fname)
                safe_fname = fname.encode('ascii', errors='replace').decode()
                safe_disp = disp.encode('ascii', errors='replace').decode() if disp else ""
                print(f"    - Attachment: '{safe_fname}' | Disposition: '{safe_disp}' | Russian Docx Match: {matched}")
            found_any = True
            
    if not found_any:
        print("No attachments found in the newest 50 unseen emails.")
        
    mail.logout()
except Exception as e:
    import traceback
    traceback.print_exc()

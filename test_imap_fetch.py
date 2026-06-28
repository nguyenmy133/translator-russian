import imaplib
import email
import sys
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("GMAIL_ADDRESS", "")
PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

if not EMAIL or not PASSWORD:
    print("[FAIL] Missing credentials in .env")
    sys.exit(1)

print(f"Connecting to IMAP for: {EMAIL}")
try:
    mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    mail.login(EMAIL, PASSWORD)
    mail.select("INBOX")
    print("Connected successfully!")
    
    # Search unseen
    status, data = mail.uid("search", None, "UNSEEN")
    if status != "OK" or not data[0]:
        print("No unseen emails.")
        mail.logout()
        sys.exit(0)
        
    all_uids = data[0].split()
    print(f"Total unseen emails: {len(all_uids)}")
    
    uids_to_check = all_uids[-50:]
    print(f"Checking newest 50 UIDs: {[uid.decode() for uid in uids_to_check]}")
    
    # Try sequential fetch to see if it hangs
    import time
    start_time = time.time()
    
    for i, uid in enumerate(reversed(uids_to_check)):
        uid_str = uid.decode()
        print(f"[{i+1}/50] Fetching UID {uid_str} header...")
        try:
            status, header_data = mail.uid(
                "fetch", uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT CONTENT-TYPE)])"
            )
            if status != "OK" or not header_data or not header_data[0]:
                print(f"  UID {uid_str}: Failed to fetch header")
                continue
                
            raw_header = header_data[0][1] if isinstance(header_data[0], tuple) else b""
            header_msg = email.message_from_bytes(raw_header)
            content_type = header_msg.get("Content-Type", "")
            print(f"  UID {uid_str}: Content-Type={content_type.strip()}")
        except Exception as e:
            print(f"  UID {uid_str} Error: {e}")
            break
            
    print(f"Sequential fetch completed in {time.time() - start_time:.2f} seconds.")
    mail.logout()
except Exception as e:
    print(f"Error: {e}")

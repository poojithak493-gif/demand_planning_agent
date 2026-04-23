import os
import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from dotenv import load_dotenv

load_dotenv()

IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

# Only distributor emails here
DISTRIBUTOR_EMAIL_TO_ID = {
    "revanbejagam@gmail.com": "D01",
    "rishithareddyc2002@gmail.com": "D02",
    "saherwardi.mustafa@gmail.com": "D03",
    "lingaphani21@gmail.com": "D04",
    "poojithak493@gmail.com": "D05",
    
}


def decode_mime_words(text):
    if not text:
        return ""
    parts = decode_header(text)
    decoded = []
    for part, enc in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(enc or "utf-8", errors="ignore"))
        else:
            decoded.append(part)
    return "".join(decoded)


def extract_email_body(msg):
    plain_text = ""
    html_text = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in content_disposition.lower():
                continue

            try:
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                if payload:
                    text = payload.decode(charset, errors="ignore")
                    if content_type == "text/plain":
                        plain_text += text + "\n"
                    elif content_type == "text/html":
                        html_text += text + "\n"
            except Exception:
                continue
    else:
        try:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or "utf-8"
            if payload:
                text = payload.decode(charset, errors="ignore")
                if msg.get_content_type() == "text/plain":
                    plain_text = text
                elif msg.get_content_type() == "text/html":
                    html_text = text
        except Exception:
            pass

    return plain_text.strip() if plain_text.strip() else html_text.strip()


def save_attachment(part, download_folder="attachments"):
    os.makedirs(download_folder, exist_ok=True)

    filename = part.get_filename()
    if not filename:
        return None

    filename = decode_mime_words(filename)
    filepath = os.path.join(download_folder, filename)

    base, ext = os.path.splitext(filepath)
    counter = 1
    while os.path.exists(filepath):
        filepath = f"{base}_{counter}{ext}"
        counter += 1

    with open(filepath, "wb") as f:
        f.write(part.get_payload(decode=True))

    return {
        "filename": os.path.basename(filepath),
        "file_path": filepath
    }


def extract_attachments(msg):
    attachments = []
    for part in msg.walk():
        content_disposition = str(part.get("Content-Disposition", ""))
        if "attachment" in content_disposition.lower():
            saved = save_attachment(part)
            if saved:
                attachments.append(saved)
    return attachments


def is_reply_mail(msg):
    subject = (msg.get("Subject") or "").strip().lower()
    in_reply_to = msg.get("In-Reply-To")
    references = msg.get("References")

    if in_reply_to or references:
        return True

    if subject.startswith("re:"):
        return True

    return False


def search_email_ids_for_sender(mail, sender_email):
    status, data = mail.search(None, f'FROM "{sender_email}"')
    if status != "OK":
        return []
    return data[0].split()


def get_latest_mail_per_distributor():
    if not EMAIL_ADDRESS:
        raise ValueError("EMAIL_ADDRESS missing in .env")
    if not EMAIL_APP_PASSWORD:
        raise ValueError("EMAIL_APP_PASSWORD missing in .env")

    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
    mail.select("inbox")

    latest_by_distributor = {}

    for sender_email, distributor_id in DISTRIBUTOR_EMAIL_TO_ID.items():
        email_ids = search_email_ids_for_sender(mail, sender_email)

        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            if status != "OK":
                continue

            for response_part in msg_data:
                if not isinstance(response_part, tuple):
                    continue

                msg = email.message_from_bytes(response_part[1])

                _, from_email = parseaddr(msg.get("From"))
                from_email = from_email.lower().strip()

                if from_email != sender_email.lower().strip():
                    continue

                if not is_reply_mail(msg):
                    continue

                try:
                    mail_date = parsedate_to_datetime(msg.get("Date"))
                except Exception:
                    mail_date = None

                subject = decode_mime_words(msg.get("Subject"))
                body = extract_email_body(msg)
                attachments = extract_attachments(msg)

                mail_data = {
                    "message_id": msg.get("Message-ID"),
                    "from_email": from_email,
                    "subject": subject,
                    "date": msg.get("Date"),
                    "parsed_date": mail_date,
                    "distributor_id": distributor_id,
                    "body": body,
                    "raw_body": body,
                    "attachments": attachments,
                }

                old = latest_by_distributor.get(distributor_id)
                if old is None:
                    latest_by_distributor[distributor_id] = mail_data
                else:
                    old_date = old.get("parsed_date")
                    if mail_date and (old_date is None or mail_date > old_date):
                        latest_by_distributor[distributor_id] = mail_data

    mail.logout()

    replies = list(latest_by_distributor.values())
    replies.sort(key=lambda x: x.get("distributor_id") or "")

    print(f"\nLatest distributor reply mails found: {len(replies)}")
    return replies


def read_unseen_replies():
    return get_latest_mail_per_distributor()


if __name__ == "__main__":
    data = get_latest_mail_per_distributor()

    for i, mail_data in enumerate(data, 1):
        print("\n" + "=" * 80)
        print(f"LATEST REPLY {i}")
        print("=" * 80)
        print("Distributor ID:", mail_data["distributor_id"])
        print("From          :", mail_data["from_email"])
        print("Subject       :", mail_data["subject"])
        print("Date          :", mail_data["date"])
        print("Attachments   :", mail_data["attachments"])
        print("Body:\n", mail_data["body"][:500] if mail_data["body"] else "No body found")
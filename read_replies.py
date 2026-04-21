import os
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))


def clean_text(text):
    if not text:
        return ""

    decoded_parts = decode_header(text)
    final_text = ""

    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            final_text += part.decode(encoding or "utf-8", errors="ignore")
        else:
            final_text += part

    return final_text


def extract_email_body(msg):
    body_text = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if "attachment" in content_disposition:
                continue

            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    body_text += payload.decode(errors="ignore")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body_text = payload.decode(errors="ignore")

    return body_text.strip()


def save_attachments(msg, save_folder="attachments"):
    saved_files = []
    os.makedirs(save_folder, exist_ok=True)

    for part in msg.walk():
        content_disposition = str(part.get("Content-Disposition"))

        if "attachment" in content_disposition:
            filename = part.get_filename()
            if filename:
                filename = clean_text(filename)
                file_path = os.path.join(save_folder, filename)

                with open(file_path, "wb") as file:
                    file.write(part.get_payload(decode=True))

                saved_files.append(file_path)

    return saved_files


def read_unseen_emails():
    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD:
        raise ValueError("EMAIL_ADDRESS or EMAIL_APP_PASSWORD is missing in .env file")

    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
    mail.select("inbox")

    status, messages = mail.search(None, "UNSEEN")
    email_ids = messages[0].split()

    print(f"Found {len(email_ids)} unread email(s).")

    all_emails = []

    for email_id in email_ids:
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        subject = clean_text(msg.get("Subject"))
        from_email = clean_text(msg.get("From"))
        body = extract_email_body(msg)
        attachments = save_attachments(msg)

        email_data = {
            "from_email": from_email,
            "subject": subject,
            "body": body,
            "attachments": attachments
        }

        all_emails.append(email_data)

        print("\n-----------------------------")
        print("From:", from_email)
        print("Subject:", subject)
        print("Body:", body[:500] if body else "No body text found")
        print("Attachments:", attachments if attachments else "No attachments")

    mail.logout()
    return all_emails


if __name__ == "__main__":
    read_unseen_emails()
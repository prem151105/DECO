import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any
import imaplib
import email
from dotenv import load_dotenv

load_dotenv()

class EmailIntegration:
    def __init__(self):
        self.smtp_server = os.getenv('GMAIL_SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('GMAIL_SMTP_PORT', 587))
        self.username = os.getenv('GMAIL_USERNAME')
        self.password = os.getenv('GMAIL_PASSWORD')
        self.email_ready = all([self.username, self.password])

    def send_notification(self, to_email: str, subject: str, body: str, attachments: List[str] = None):
        """Send email notification about processed documents"""
        if not self.email_ready:
            return {"status": "error", "message": "Email not configured"}

        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        if attachments:
            for attachment in attachments:
                if os.path.exists(attachment):
                    with open(attachment, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment)}')
                        msg.attach(part)

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            text = msg.as_string()
            server.sendmail(self.username, to_email, text)
            server.quit()
            return {"status": "success", "message": f"Email sent to {to_email}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def fetch_emails(self, folder: str = 'INBOX', limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent emails for document ingestion"""
        if not self.email_ready:
            return []

        try:
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(self.username, self.password)
            mail.select(folder)

            status, messages = mail.search(None, 'ALL')
            email_ids = messages[0].split()[-limit:] if messages[0] else []

            emails = []
            for email_id in email_ids:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                raw_email = msg_data[0][1]
                email_message = email.message_from_bytes(raw_email)

                email_data = {
                    'subject': email_message['Subject'],
                    'from': email_message['From'],
                    'date': email_message['Date'],
                    'body': self._get_email_body(email_message),
                    'attachments': self._get_attachments(email_message)
                }
                emails.append(email_data)

            mail.logout()
            return emails
        except Exception as e:
            print(f"Email fetch error: {e}")
            return []

    def _get_email_body(self, email_message):
        """Extract plain text body from email"""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == 'text/plain':
                    return part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            return email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
        return ""

    def _get_attachments(self, email_message) -> List[str]:
        """Extract attachments and save them temporarily"""
        attachments = []
        for part in email_message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            filename = part.get_filename()
            if filename:
                filepath = os.path.join('temp_attachments', filename)
                os.makedirs('temp_attachments', exist_ok=True)
                with open(filepath, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                attachments.append(filepath)
        return attachments

    def route_document(self, document_data: Dict[str, Any], recipients: List[str]):
        """Route processed document to specific users via email"""
        subject = f"KMRL Document Processed: {document_data.get('filename', 'Unknown')}"
        body = f"""
        <h3>Document Analysis Complete</h3>
        <p><strong>Filename:</strong> {document_data.get('filename')}</p>
        <p><strong>Type:</strong> {document_data.get('metadata', {}).get('doc_type')}</p>
        <p><strong>Compliance Flags:</strong> {', '.join(document_data.get('compliance', []))}</p>
        <p>Please review the attached analysis.</p>
        """
        # In a real implementation, attach the processed document
        return self.send_notification(','.join(recipients), subject, body)
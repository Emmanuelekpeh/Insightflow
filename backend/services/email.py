from mailersend import emails
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize MailerSend client
MAILERSEND_API_KEY = os.getenv("MAILERSEND_API_KEY")
mailer = emails.NewEmail(MAILERSEND_API_KEY)

async def send_email(to_email: str, subject: str, html_content: str, from_email: str = "noreply@yourdomain.com"):
    """
    Send an email using MailerSend
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        html_content (str): HTML content of the email
        from_email (str, optional): Sender email address. Defaults to noreply@yourdomain.com.
    
    Returns:
        dict: Response from MailerSend API
    """
    # Create recipients list
    recipients = [{"email": to_email}]
    
    # Create email data
    mail_body = {
        "from": {
            "email": from_email,
            "name": "InsightFlow"
        },
        "to": recipients,
        "subject": subject,
        "html": html_content
    }
    
    try:
        # Send the email
        return mailer.send(mail_body)
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        raise e 
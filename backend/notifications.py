import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


logger = logging.getLogger(__name__)


def send_notification(product, current_price, user_price, user_contact):
    if current_price >= user_price:
        return

    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_PASS")

    if not email_user or not email_pass:
        logger.error("Email credentials are not set. Please set EMAIL_USER and EMAIL_PASS.")
        return

    msg = MIMEMultipart()
    msg["From"] = email_user
    msg["To"] = user_contact
    msg["Subject"] = f"Price Drop Alert: {product}"

    body = f"The price of {product} has dropped to Rs.{current_price}."
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email_user, email_pass)
        server.sendmail(email_user, user_contact, msg.as_string())
        server.quit()
        logger.info(f"Notification sent to {user_contact} for {product}.")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

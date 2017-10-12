import smtplib
import argparse
from . import app

message_template = """From: Ryan <{from_address}>
To: {to_name} <{to_address}>
Subject: {subject}
Content-type: text/html

{message_content}
"""

def send_email(to_address, to_name, subject, message_content):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(app.config['EMAIL_ADDRESS'], app.config['EMAIL_PASSWORD'])
    message = message_template.format(
        from_address=app.config['EMAIL_ADDRESS'],
        to_address=to_address,
        to_name=to_name,
        subject=subject,
        message_content=message_content,
    )

    try:
       server.sendmail(app.config['EMAIL_ADDRESS'], to_address, message)
       print("Successfully sent email to {}".format(to_address))
    except smtplib.SMTPException as e:
       print("Error: unable to send email to {}".format(to_address))
       print(e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Link checker')
    parser.add_argument('-e', '--to-email', help='Recipient\'s email address', required=True)
    parser.add_argument('-n', '--to-name', help='Recipient\'s name', required=True)
    parser.add_argument('-s', '--subject', help='Email subject line', required=True)
    parser.add_argument('-m', '--message', help='HTML message content', required=True)
    args = parser.parse_args()
    send_email(
        to_address=args.to_email,
        to_name=args.to_name,
        subject=args.subject,
        message_content=args.message,
    )

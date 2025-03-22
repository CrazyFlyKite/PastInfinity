import smtplib
from email.message import EmailMessage
from pathlib import Path

from utilities import PathLikeString


def send_email(email: str, password: str, subject: str, content: str, attachment: PathLikeString) -> None:
	# Basic setup
	message: EmailMessage = EmailMessage()
	message['Subject'] = subject
	message['From'] = email
	message['To'] = email
	message.set_content(content)

	# Adding attachment
	with open(attachment, 'rb') as file:
		attachment_data = file.read()
		filename = Path(attachment).name
		message.add_attachment(attachment_data, maintype='application', subtype='octet-stream', filename=filename)

	# Send
	with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
		smtp.ehlo()
		smtp.starttls()
		smtp.ehlo()

		smtp.login(email, password)
		smtp.send_message(message)

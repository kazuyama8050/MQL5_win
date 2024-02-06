import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

class MailHandler():
    FROM_ADDRESS = "kazuki118050@gmail.com"
    TO_ADDRESS = "kazuki118050@gmail.com"
    MY_PASSWORD = "bsok wlbz usbr lpse"

    @staticmethod
    def send_mail(subject, mail_body):
        try:
            msg = MIMEText(mail_body)
            msg["Subject"] = subject
            msg["From"] = MailHandler.FROM_ADDRESS
            msg["To"] = MailHandler.TO_ADDRESS

            smtpobj = smtplib.SMTP("smtp.gmail.com", 587)
            smtpobj.ehlo()
            smtpobj.starttls()
            smtpobj.ehlo()
            smtpobj.login(MailHandler.FROM_ADDRESS, MailHandler.MY_PASSWORD)
            smtpobj.sendmail(MailHandler.FROM_ADDRESS, MailHandler.TO_ADDRESS, msg.as_string())
            smtpobj.close()
            return True
        except:
            return False
        
    @staticmethod
    def read_mail_body_template(filepath):
        with open(filepath, "r", encoding="utf-8") as file:
            mail_body_template = file.read()
        return mail_body_template
from app.services.parser_service import traiter_mail

mail_exemple = """
Hello,

Store PRK0229

Card payment declined.

Engineer should replace Lane3000.
"""

ticket = traiter_mail(mail_exemple)

print(ticket)
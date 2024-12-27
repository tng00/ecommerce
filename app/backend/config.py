



# import smtplib
# from email.mime.text import MIMEText

# SMTP_CONFIG = {
#     "host": "smtp.yandex.com",  # SMTP-сервер
#     "port": 587,              # Порт TLS
#     "username": "nick.seriy@yandex.ru",
#     "password": "uxlxfwgccfxswjzj",  # Пароль приложения
#     "from_email": "nick.seriy@yandex.ru",   # Email отправителя
# }


# def send_test_email():
#     message = MIMEText("Это тестовое сообщение.")
#     message["Subject"] = "Тестовое письмо"
#     message["From"] = SMTP_CONFIG["from_email"]
#     message["To"] = "nick.seriy@yandex.ru"

#     try:
#         with smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"]) as server:
#             server.starttls()
#             server.login(SMTP_CONFIG["username"], SMTP_CONFIG["password"])
#             server.sendmail(
#                 SMTP_CONFIG["from_email"],
#                 "nick.seriy@yandex.ru",
#                 message.as_string(),
#             )
#             print("Письмо успешно отправлено")
#     except Exception as e:
#         print(f"Ошибка отправки: {e}")

# send_test_email()
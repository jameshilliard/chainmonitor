SENDER_EMAIL = 'errors@example.com'
RECEIVER_EMAIL = 'me@example.com'
SMTP_SERVER = 'smtp.server.com'
SMTP_USER = SENDER_EMAIL.split('@')[0] # or 'user@example.com'
SMTP_PASSWORD = 'password'
SMTP_USE_TLS = True
SMTP_PORT = 587 if SMTP_USE_TLS else 25

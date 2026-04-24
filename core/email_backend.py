import ssl
from django.core.mail.backends.smtp import EmailBackend

class UnverifiedEmailBackend(EmailBackend):
    def open(self):
        if self.connection:
            return False
        try:
            # Bypass SSL verification
            self.connection = self.connection_class(self.host, self.port, timeout=self.timeout)
            if self.use_tls:
                # This is the magic part: passing an unverified context to starttls
                context = ssl._create_unverified_context()
                self.connection.starttls(context=context)
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except Exception:
            if not self.fail_silently:
                raise
            return False

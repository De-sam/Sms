from django.contrib.auth.tokens import PasswordResetTokenGenerator
from datetime import datetime, timedelta

class CustomPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    TOKEN_TIMEOUT_SECONDS = 300  # Token expires after 5 minutes

    def _make_timestamp(self):
        return int((datetime.now() - datetime(2001, 1, 1)).total_seconds())

    def check_token(self, user, token):
        if not (user and token):
            return False

        try:
            ts_b36, _ = token.split("-")
            timestamp = int(ts_b36, 36)
        except ValueError:
            return False

        current_timestamp = self._make_timestamp()
        if current_timestamp - timestamp > self.TOKEN_TIMEOUT_SECONDS:
            return False

        return super().check_token(user, token)

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from datetime import datetime, timedelta

class CustomPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    TOKEN_TIMEOUT_SECONDS = 60  # Token expires after 1 minute

    def _make_timestamp(self):
        """
        Overriding the timestamp method to calculate the token age.
        """
        return int((datetime.now() - datetime(2001, 1, 1)).total_seconds())

    def check_token(self, user, token):
        """
        Check that a token is valid and not expired.
        """
        if not (user and token):
            return False

        try:
            ts_b36, _ = token.split("-")
            timestamp = int(ts_b36, 36)
        except ValueError:
            return False

        # Check token age
        current_timestamp = self._make_timestamp()
        if current_timestamp - timestamp > self.TOKEN_TIMEOUT_SECONDS:
            return False

        # Validate token using Django's built-in logic
        return super().check_token(user, token)

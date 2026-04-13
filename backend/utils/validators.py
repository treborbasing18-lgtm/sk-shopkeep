import re

class Validators:

    @staticmethod
    def validate_username(username):
        if not username or len(username.strip()) < 3:
            return False, "Username must be at least 3 characters"
        if len(username.strip()) > 32:
            return False, "Username must be 32 characters or fewer"
        if not re.match(r'^[a-zA-Z0-9_]+$', username.strip()):
            return False, "Username may only contain letters, numbers, and underscores"
        return True, None

    @staticmethod
    def validate_password(password):
        if not password or len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not re.search(r'[A-Za-z]', password):
            return False, "Password must contain at least one letter"
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        COMMON = {'password', 'password1', '12345678', '123456789', 'qwerty123', 'iloveyou'}
        if password.lower() in COMMON:
            return False, "Password is too common"
        return True, None

    @staticmethod
    def validate_price(price):
        try:
            value = float(price)
        except (TypeError, ValueError):
            return False, "Price must be a number"
        if value < 0:
            return False, "Price must be non-negative"
        return True, None

    @staticmethod
    def validate_quantity(quantity):
        try:
            value = int(quantity)
        except (TypeError, ValueError):
            return False, "Quantity must be a whole number"
        if value < 0:
            return False, "Quantity must be non-negative"
        return True, None

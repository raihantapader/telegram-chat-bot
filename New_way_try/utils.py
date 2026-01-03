import secrets
import string

_ALPHABET = string.ascii_uppercase + string.digits

def generate_test_id(length: int = 6) -> str:
    # Example: 305B2E
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))

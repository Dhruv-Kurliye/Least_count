import hashlib
import secrets

from jose import jwt

SECRET_KEY = "SUPER_SECRET_KEY"
ALGORITHM = "HS256"

HASH_ITERATIONS = 260000


def hash_password(password):
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        HASH_ITERATIONS
    ).hex()

    return f"pbkdf2_sha256${salt}${password_hash}"


def verify_password(plain, hashed):
    try:
        algorithm, salt, saved_hash = hashed.split("$", 2)

        if algorithm != "pbkdf2_sha256":
            return False

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            plain.encode("utf-8"),
            salt.encode("utf-8"),
            HASH_ITERATIONS
        ).hex()

        return secrets.compare_digest(password_hash, saved_hash)
    except Exception:
        return False


def create_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        return None

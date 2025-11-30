# app/utils/security.py
# from passlib.context import CryptContext

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# def hash_password(password: str) -> str:  # $2b$12$...длинная строка...
#     return pwd_context.hash(password)


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)


from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _truncate_password(password: str) -> str:
    # bcrypt ограничен 72 байтами, поэтому обрезаем по байтам
    raw = password.encode("utf-8")
    if len(raw) > 72:
        raw = raw[:72]
    return raw.decode("utf-8", errors="ignore")


def hash_password(password: str) -> str:
    safe = _truncate_password(password)
    return pwd_context.hash(safe)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    safe = _truncate_password(plain_password)
    return pwd_context.verify(safe, hashed_password)

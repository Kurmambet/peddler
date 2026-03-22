# backend\app\core\exceptions.py
from fastapi import HTTPException, status


class ChatAccessDenied(HTTPException):
    """Пользователь не имеет доступа к чату"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN, detail="You are not a participant of this chat"
        )


class ChatNotFound(HTTPException):
    """Чат не найден"""

    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")


class UserNotFound(HTTPException):
    """Пользователь не найден"""

    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

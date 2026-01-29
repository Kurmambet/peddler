from typing import Any, Dict

from pydantic import BaseModel


class TusHookRequest(BaseModel):
    # Tusd шлет много полей, нам важны ID и MetaData
    ID: str
    Upload: Dict[str, Any]
    # Внутри Upload есть 'MetaData' (словарь)
    # Пример структуры:
    # {
    #   "ID": "...",
    #   "Upload": {
    #       "ID": "...",
    #       "Size": 12345,
    #       "MetaData": {
    #           "filename": "...",
    #           "chat_id": "...",
    #           "token": "..."
    #       },
    #       "Storage": { "Path": "..." }
    #   }
    # }

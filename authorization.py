from datetime import datetime, timedelta
from secrets import token_hex
from typing import Dict
from config import settings


class Token:
    def __init__(self, minutes: int = settings.token_duration):
        self._token = token_hex(32)
        self._time_stamp = datetime.now()
        self._duration = timedelta(minutes=minutes)

    def valid(self) -> bool:
        return self._time_stamp+self._duration >= datetime.now()

    def __repr__(self):
        return self._token


class Authorization:
    def __init__(self):
        self._dict_tokens: Dict[str, Token] = dict()

    def add(self) -> str:
        token = Token()
        self._dict_tokens[str(token)] = token
        return str(token)

    def verify(self, key: str) -> bool:
        token = self._dict_tokens.get(key)
        if token:
            if token.valid():
                return True
            else:
                self._dict_tokens.pop(str(token))
        return False

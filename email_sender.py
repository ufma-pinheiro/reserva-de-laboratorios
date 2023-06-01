# Install Courier SDK: pip install trycourier
from trycourier import Courier
from config import settings
from pydantic import EmailStr
from typing import Dict

client = Courier(auth_token=settings.courier_api_key)


def send(dest: EmailStr, title: str, body: str, data: Dict[str, str] = dict()):
    resp = client.send_message(
        message={
            "to": {
                "email": dest
            },
            "content": {
                "title": title,
                "body": body
            },
            "data": data
        }
    )

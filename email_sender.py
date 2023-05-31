# Install Courier SDK: pip install trycourier
from trycourier import Courier
from config import settings

client = Courier(auth_token=settings.courier_api_key)

resp = client.send_message(
    message={
        "to": {
            "email": settings.admin_email
        },
        "content": {
            "title": "Welcome to Courier!",
            "body": "Want to hear a joke? {{joke}}"
        },
        "data": {
            "joke": "Why does Python live on land? Because it is above C level"
        }
    }
)

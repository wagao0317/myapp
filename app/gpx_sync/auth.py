from pathlib import Path
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

BASE_DIR = Path(__file__).parent

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly"
]

token_path = BASE_DIR / "token.json"
client_secret_path = BASE_DIR / "client_secret.json"

creds = None

if token_path.exists():
    creds = Credentials.from_authorized_user_file(
        token_path,
        SCOPES,
    )

if not creds or not creds.valid:

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secret_path,
            SCOPES,
        )

        creds = flow.run_local_server(port=0)

    with open(token_path, "w") as token:
        token.write(creds.to_json())

print("認証完了")
print(token_path)
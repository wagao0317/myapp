from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).parent

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly"
]

creds = Credentials.from_authorized_user_file(
    BASE_DIR / "token.json",
    SCOPES,
)

service = build(
    "drive",
    "v3",
    credentials=creds,
)

results = service.files().list(
    pageSize=20,
).execute()

for file in results.get("files", []):
    print(file["name"])
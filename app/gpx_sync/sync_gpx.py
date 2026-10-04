import io
import json
from pathlib import Path

import requests

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


# =========================
# 設定
# =========================

FOLDER_ID = "1cF0mH05EaXSh31MTSozrn_qUs3BA5LzU"

UPLOAD_URL = "http://localhost:8000/upload"

BASE_DIR = Path(__file__).parent

TOKEN_FILE = BASE_DIR / "token.json"

PROCESSED_FILE = BASE_DIR / "processed_files.json"

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly"
]


# =========================
# 認証
# =========================

creds = Credentials.from_authorized_user_file(
    TOKEN_FILE,
    SCOPES,
)

service = build(
    "drive",
    "v3",
    credentials=creds,
)


# =========================
# 処理済みファイル読込
# =========================

if PROCESSED_FILE.exists():
    with open(PROCESSED_FILE, "r") as f:
        processed = set(json.load(f))
else:
    processed = set()


# =========================
# Drive内GPX取得
# =========================

results = service.files().list(
    q=f"'{FOLDER_ID}' in parents and trashed=false",
    fields="files(id,name)",
).execute()

files = results.get("files", [])


# =========================
# 新規GPXのみ処理
# =========================

for file in files:

    file_id = file["id"]
    file_name = file["name"]

    if not file_name.lower().endswith(".gpx"):
        continue

    if file_id in processed:
        continue

    print(f"Downloading: {file_name}")

    request = service.files().get_media(
        fileId=file_id,
    )

    buffer = io.BytesIO()

    downloader = MediaIoBaseDownload(
        buffer,
        request,
    )

    done = False

    while not done:
        _, done = downloader.next_chunk()

    gpx_bytes = buffer.getvalue()

    print(f"Uploading: {file_name}")

    response = requests.post(
        UPLOAD_URL,
        files={
            "file": (
                file_name,
                gpx_bytes,
                "application/gpx+xml",
            )
        },
        timeout=60,
    )

    response.raise_for_status()

    print(response.json())

    processed.add(file_id)


# =========================
# 保存
# =========================

with open(PROCESSED_FILE, "w") as f:
    json.dump(
        list(processed),
        f,
        indent=2,
    )

print("Sync complete")
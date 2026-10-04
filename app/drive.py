from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly"
]

flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret.json",
    SCOPES,
)

creds = flow.run_local_server(port=0)
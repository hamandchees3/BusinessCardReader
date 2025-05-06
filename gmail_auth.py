from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

flow = InstalledAppFlow.from_client_secrets_file(
    "credentials.json", SCOPES
)

# ★  set an explicit redirect URI that matches credentials.json
flow.redirect_uri = "http://localhost"

# ★  build URL – now redirect_uri will be included
auth_url, _ = flow.authorization_url(
    prompt="consent",
    access_type="offline",          # get refresh token
    include_granted_scopes="true"
)

print("\nSTEP 1 ➜ Open this link, accept, let it fail to load localhost:\n")
print(auth_url)

redirect_response = input(
    "\nSTEP 2 ➜ Copy the FULL redirected URL from the browser’s address bar\n"
    "          (it starts with http://localhost/?code=…) and paste it here:\n"
).strip()

flow.fetch_token(authorization_response=redirect_response)
creds = flow.credentials
Path("token.json").write_text(creds.to_json())
print("\n✅  token.json created — Gmail drafts are now unlocked!")

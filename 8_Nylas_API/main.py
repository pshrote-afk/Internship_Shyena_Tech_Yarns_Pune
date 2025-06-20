import os
import urllib.parse


client_id = os.getenv("NYLAS_CLIENT_ID")
redirect_uri = os.getenv("NYLAS_CALLBACK_URI")
login_hint = "pdshrote@gcoen.ac.in"

params = {
    "client_id": client_id,
    "response_type": "code",
    "scope": "email.read_only",  # or "email.read_only,email.send"
    "redirect_uri": redirect_uri,
    "login_hint": login_hint,
}

url = "https://api.nylas.com/oauth/authorize?" + urllib.parse.urlencode(params)
print("Visit this URL to authenticate:\n", url)

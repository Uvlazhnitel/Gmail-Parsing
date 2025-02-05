import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scope (grants read-only access to Gmail)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    """Function for authentication in Gmail API"""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If no token exists, request a new one
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Save the token to avoid logging in again
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

if __name__ == "__main__":
    creds = authenticate_gmail()
    print("✅ Authentication successful!")
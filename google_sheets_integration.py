import os
import gspread
from google.oauth2.service_account import Credentials

# Helper to get credentials path
def get_google_creds_path():
    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    if creds_json:
        temp_path = '/tmp/google_creds.json'
        with open(temp_path, 'w') as f:
            f.write(creds_json)
        return temp_path
    else:
        return 'visiting-card-reader-465216-4600e9621451.json'

# Initialize Google Sheets
def init_gsheet():
    scopes = ['https://www.googleapis.com/auth/spreadsheets',
              'https://www.googleapis.com/auth/drive']
    creds_path = get_google_creds_path()
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    return gspread.authorize(creds)

def append_to_master_sheet(card_data):
    try:
        gc = init_gsheet()
        sheet = gc.open("All_Visiting_Cards_Master").sheet1  # open master sheet

        # Handle uploaded_at field safely (not needed in new format)
        # Map card_data to the required columns, using empty string if missing
        row = [
            card_data.get("name", ""),                    # Name
            card_data.get("email", ""),                   # Email
            card_data.get("company", ""),                 # Company/Institute
            card_data.get("phone", ""),                   # Contact
            card_data.get("address", ""),                 # Location
            card_data.get("type", ""),                    # Type (may be missing)
            card_data.get("designation", ""),             # Designation
            card_data.get("website", ""),                 # Website
            card_data.get("additional_info", "")           # Additional Info
        ]
        sheet.append_row(row)
        return True
    except Exception as e:
        print(f"Google Sheets Error: {e}")
        return False 

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
        
        # Handle uploaded_at field safely
        uploaded_at = card_data.get("uploaded_at")
        if uploaded_at:
            formatted_date = uploaded_at.strftime("%Y-%m-%d %H:%M:%S")
        else:
            formatted_date = ""
        
        sheet.append_row([
            card_data.get("name", ""),
            card_data.get("company", ""),
            card_data.get("designation", ""),
            card_data.get("email", ""),
            card_data.get("phone", ""),
            card_data.get("address", ""),
            card_data.get("website", ""),
            card_data.get("additional_info", ""),
            card_data.get("scanned_by", ""),
            formatted_date
        ])
        return True
    except Exception as e:
        print(f"Google Sheets Error: {e}")
        return False 

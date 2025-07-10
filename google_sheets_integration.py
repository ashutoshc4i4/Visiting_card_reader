import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google
import googleapiclient

# Google Sheets API scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

ALLOWED_SHEET_USER = 'ashutosh.lab@c4i4.com'

class GoogleSheetsIntegration:
    def __init__(self):
        self.creds = None
        self.service = None
        self.token_path = 'token.pickle'
        self.credentials_path = 'credentials.json'
        # Default spreadsheet ID for storing all visiting card data
        self.default_spreadsheet_id = '1C2HQUijh7nSobcRw3ALuU55pUkHvmR20ad4yzWGgQc8'
        # Service account email
        self.service_account_email = 'python-api@visiting-card-reader-465216.iam.gserviceaccount.com'
        self.service_account_path = 'visiting-card-reader-465216-1554a8393478.json'
    
    def authenticate(self):
        """Authenticate with Google Sheets API using service account"""
        try:
            if not os.path.exists(self.service_account_path):
                raise FileNotFoundError(
                    f"Service account key file '{self.service_account_path}' not found. "
                    "Please download the service account key from Google Cloud Console."
                )
            
            # Load service account credentials
            self.creds = service_account.Credentials.from_service_account_file(
                self.service_account_path, scopes=SCOPES)
            
            # Build the service
            self.service = build('sheets', 'v4', credentials=self.creds)
            return True
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def create_spreadsheet(self, title):
        """Create a new Google Spreadsheet"""
        try:
            if not self.service:
                self.authenticate()
            
            spreadsheet = {
                'properties': {
                    'title': title
                },
                'sheets': [
                    {
                        'properties': {
                            'title': 'Visiting Cards',
                            'gridProperties': {
                                'rowCount': 1000,
                                'columnCount': 10
                            }
                        }
                    }
                ]
            }
            
            spreadsheet = self.service.spreadsheets().create(body=spreadsheet).execute()
            return spreadsheet['spreadsheetId']
        
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
    
    def append_card_data(self, spreadsheet_id, card_data):
        """Append visiting card data to Google Sheets"""
        try:
            if not self.service:
                self.authenticate()
            
            # Prepare the data row
            values = [[
                card_data.get('name', ''),
                card_data.get('company', ''),
                card_data.get('designation', ''),
                card_data.get('email', ''),
                card_data.get('phone', ''),
                card_data.get('address', ''),
                card_data.get('website', ''),
                card_data.get('additional_info', ''),
                str(card_data.get('uploaded_at', '')),
                card_data.get('scanned_by', '')
            ]]
            
            body = {
                'values': values
            }
            
            # Append to the first sheet
            result = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A:J',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            return result
        
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
    
    def get_spreadsheet_data(self, spreadsheet_id, range_name='Sheet1!A:J'):
        """Get data from Google Sheets"""
        try:
            if not self.service:
                self.authenticate()
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            return result.get('values', [])
        
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
    
    def update_headers(self, spreadsheet_id):
        """Update the header row of the spreadsheet"""
        try:
            if not self.service:
                self.authenticate()
            
            headers = [
                'Name', 'Company', 'Designation', 'Email', 'Phone',
                'Address', 'Website', 'Additional Info', 'Uploaded At', 'Scanned By'
            ]
            
            body = {
                'values': [headers]
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A1:J1',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return result
        
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
    
    def export_to_default_sheet(self, card_data):
        """Export card data to the default spreadsheet"""
        try:
            if not self.service:
                self.authenticate()
            
            # First, ensure headers are set up
            self.update_headers(self.default_spreadsheet_id)
            
            # Then append the card data
            result = self.append_card_data(self.default_spreadsheet_id, card_data)
            return result
        
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
    
    def get_default_spreadsheet_id(self):
        """Get the default spreadsheet ID"""
        return self.default_spreadsheet_id

# Global instance
sheets_integration = GoogleSheetsIntegration() 

# ... existing code ...
def write_to_google_sheets(card_data):
    try:
        print(f"[DEBUG] Attempting to write to Google Sheets for user: {card_data.get('scanned_by')}")
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        credentials = Credentials.from_service_account_file(GOOGLE_SHEETS_KEY_FILE, scopes=scopes)
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key(GOOGLE_SHEET_ID)
        worksheet = sh.sheet1  # or use .worksheet('Sheet1') if named
        row = [
            card_data.get('name', ''),
            card_data.get('company', ''),
            card_data.get('designation', ''),
            card_data.get('email', ''),
            card_data.get('phone', ''),
            card_data.get('website', ''),
            card_data.get('address', ''),
            card_data.get('additional_info', ''),
            str(card_data.get('uploaded_at', '')),
            card_data.get('original_filename', '')
        ]
        print(f"[DEBUG] Row to append: {row}")
        worksheet.append_row(row, value_input_option='USER_ENTERED')
        print("[DEBUG] Successfully wrote to Google Sheets.")
    except Exception as e:
        print(f"[ERROR] Failed to write to Google Sheets: {e}")
        import traceback
        traceback.print_exc()
# ... existing code ...

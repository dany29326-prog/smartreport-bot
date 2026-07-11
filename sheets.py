import gspread
from google.oauth2.service_account import Credentials
import json
import os
from datetime import datetime

class GoogleSheetsManager:
    def __init__(self, service_account_json=None):
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]
        
        if service_account_json:
            self.creds_info = json.loads(service_account_json)
        else:
            creds_file = os.getenv('SERVICE_ACCOUNT_FILE', 'service_account.json')
            with open(creds_file, 'r') as f:
                self.creds_info = json.load(f)
        
        self.sheet_id = os.getenv('SHEET_ID')
        if not self.sheet_id:
            raise ValueError("SHEET_ID not found in environment variables")
        
        self._init_client()
        self._setup_worksheet()
    
    def _init_client(self):
        try:
            self.creds = Credentials.from_service_account_info(
                self.creds_info,
                scopes=self.scopes
            )
            self.client = gspread.authorize(self.creds)
            print("✅ Service Account authenticated successfully")
        except Exception as e:
            print(f"❌ Authentication failed: {str(e)}")
            raise
    
    def _setup_worksheet(self):
        try:
            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            try:
                self.worksheet = self.spreadsheet.worksheet("Keuangan")
                print("✅ Worksheet 'Keuangan' found")
            except gspread.exceptions.WorksheetNotFound:
                self.worksheet = self.spreadsheet.add_worksheet(
                    title="Keuangan",
                    rows="1000",
                    cols="5"
                )
                print("✅ Worksheet 'Keuangan' created")
                self._initialize_headers()
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"❌ Spreadsheet not found. Check SHEET_ID: {self.sheet_id}")
            raise
    
    def _initialize_headers(self):
        headers = ['Tanggal', 'Kategori', 'Pemasukan', 'Pengeluaran', 'Keterangan']
        self.worksheet.append_row(headers)
        print("✅ Headers initialized")
    
    def add_transaction(self, trans_type, amount, category, description):
        try:
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
            
            if trans_type == 'pemasukan':
                row_data = [date_str, category, str(amount), "0", description]
            else:
                row_data = [date_str, category, "0", str(amount), description]
            
            self.worksheet.append_row(row_data)
            return {
                'date': date_str,
                'type': trans_type,
                'amount': amount,
                'category': category,
                'description': description,
                'timestamp': timestamp
            }
        except Exception as e:
            print(f"❌ Failed to add transaction: {str(e)}")
            raise
    
    def get_transactions(self, limit=1000):
        try:
            records = self.worksheet.get_all_records()
            if not records:
                return []
            records.reverse()
            if limit and len(records) > limit:
                records = records[:limit]
            return records
        except Exception as e:
            print(f"❌ Failed to get transactions: {str(e)}")
            raise
    
    def get_summary(self):
        try:
            records = self.worksheet.get_all_records()
            total_masuk = sum(float(r['Pemasukan']) for r in records)
            total_keluar = sum(float(r['Pengeluaran']) for r in records)
            saldo = total_masuk - total_keluar
            return {
                'total_masuk': total_masuk,
                'total_keluar': total_keluar,
                'saldo': saldo
            }
        except Exception as e:
            print(f"❌ Failed to get summary: {str(e)}")
            return {'total_masuk': 0, 'total_keluar': 0, 'saldo': 0}
    
    def test_connection(self):
        try:
            title = self.worksheet.title
            print(f"✅ Connected to Google Sheets: {title}")
            return True
        except Exception as e:
            print(f"❌ Connection test failed: {str(e)}")
            return False
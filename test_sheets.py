import os
from dotenv import load_dotenv
from sheets import GoogleSheetsManager

load_dotenv()

def test_connection():
    print("🔍 Testing Google Sheets connection...")
    
    try:
        service_account_json = os.getenv('SERVICE_ACCOUNT_JSON')
        
        if service_account_json:
            print("Using SERVICE_ACCOUNT_JSON from environment")
            manager = GoogleSheetsManager(service_account_json)
        else:
            print("Using local service_account.json file")
            manager = GoogleSheetsManager()
        
        if manager.test_connection():
            print("✅ Connection successful!")
            
            print("\n📝 Testing add expense...")
            result = manager.add_expense(1000, "Test User", "Test", "Test expense")
            print(f"✅ Test expense added: {result}")
            
            print("\n📊 Testing get expenses...")
            expenses = manager.get_expenses(limit=5)
            print(f"✅ Found {len(expenses)} expenses")
            for exp in expenses:
                print(f"  - {exp['Nama']}: Rp{float(exp['Jumlah']):,.0f} ({exp['Kategori']})")
            
            total = manager.get_total_expenses()
            print(f"\n💰 Total expenses: Rp{total:,.0f}")
            
            print("\n✅ All tests passed!")
        else:
            print("❌ Connection failed!")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n📋 Troubleshooting:")
        print("1. Check if service_account.json exists")
        print("2. Verify SHEET_ID is correct")
        print("3. Ensure Service Account email is shared with the sheet")

if __name__ == "__main__":
    test_connection()
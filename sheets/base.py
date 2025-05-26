# ==== sheets/base.py ====
# Google Sheets API ашиглан sheet-үүдтэй холбогддог үндсэн функц
import gspread
from google.oauth2.service_account import Credentials
from config import CREDS_FILE, SCOPES

def get_sheet(url):
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(url).sheet1
    return sheet

# Google Sheets-ээс оффисуудын мэдээлэл авах utility функц энд байна.

def get_offices_from_sheet(sheet_url, creds_file='credentials.json', worksheet_name="offices"):
    gc = gspread.service_account(filename=creds_file)
    sh = gc.open_by_url(sheet_url)
    worksheet = sh.worksheet(worksheet_name)
    data = worksheet.get_all_records()
    offices = []
    for row in data:
        try:
            if not row['lat'] or not row['lon']:
                continue
            offices.append({
                'name': row['name'],
                'lat': float(row['lat']),
                'lon': float(row['lon'])
            })
        except Exception as e:
            print(f"Алдаатай мөр алгасав: {row} ({e})")
    return offices

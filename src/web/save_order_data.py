import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Подключение к Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google-credentials.json", scope)
client = gspread.authorize(creds)

# Только ID таблицы, без URL
SHEET_ID = "1Z-m7fQwpU2_YJ8-HG4AuzSKHt_AD9eZ9D4uXlDH3flc"
sheet = client.open_by_key(SHEET_ID).sheet1

def save_web_order_data(order_data):
    row = [
        order_data.get("company", ""),
        order_data.get("passengers", ""),
        order_data.get("price", ""),
        order_data.get("status", ""),
        order_data.get("booking_start", ""),
        order_data.get("booking_end", ""),
        order_data.get("duration_hours", ""),
        order_data.get("total_price", ""),
        order_data.get("type", ""),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ]
    sheet.append_row(row)
    print("Заказ добавлен в Google Таблицу")

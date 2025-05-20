import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# 1. Получаем JSON из переменной окружения
json_data = os.environ.get("GOOGLE_CREDENTIALS_JSON")

if not json_data:
    raise Exception("GOOGLE_CREDENTIALS_JSON переменная не найдена")

# 2. Сохраняем временный файл
TEMP_CREDENTIALS_FILE = "temp_google_creds.json"
with open(TEMP_CREDENTIALS_FILE, "w") as f:
    f.write(json_data)

# 3. Авторизуемся
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(TEMP_CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)

# 4. Открываем таблицу
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

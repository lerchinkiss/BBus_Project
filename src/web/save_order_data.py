import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Получаем JSON из переменной окружения
json_data = os.environ.get("GOOGLE_CREDENTIALS_JSON")
if not json_data:
    raise Exception("❌ GOOGLE_CREDENTIALS_JSON переменная не найдена")

# Сохраняем временный JSON-файл
TEMP_CREDENTIALS_FILE = "temp_google_creds.json"
with open(TEMP_CREDENTIALS_FILE, "w") as f:
    f.write(json_data)

# Авторизация
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(TEMP_CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)

# Google Таблица
SHEET_ID = "1Z-m7fQwpU2_YJ8-HG4AuzSKHt_AD9eZ9D4uXlDH3flc"
sheet = client.open_by_key(SHEET_ID).sheet1

def save_order_data(order_data):
    try:
        # Используем даты напрямую, так как они уже в нужном формате
        booking_start = order_data.get("booking_start", "")
        booking_end = order_data.get("booking_end", "")
        
        row = [
            order_data.get("company", ""),
            order_data.get("passengers", ""),
            order_data.get("price", ""),
            order_data.get("status", ""),
            booking_start,
            booking_end,
            order_data.get("duration_hours", ""),
            order_data.get("total_price", ""),
            order_data.get("vehicle_type", "") or order_data.get("type", ""),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        sheet.append_row(row)
        print("Заказ добавлен в Google Таблицу")
    except Exception as e:
        print(f"Ошибка при сохранении заказа: {str(e)}")
        raise

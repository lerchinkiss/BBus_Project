import os
import json
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

# Получение пути к JSON
temp_path = os.environ.get("GOOGLE_CREDENTIALS_JSON")
if not temp_path or not os.path.exists(temp_path):
    raise Exception("Переменная окружения GOOGLE_CREDENTIALS_JSON не задана или файл не найден.")

print("Путь к JSON:", temp_path)
print("Файл существует?", os.path.exists(temp_path))
print("Размер файла:", os.path.getsize(temp_path))
with open(temp_path, "r", encoding="utf-8") as f:
    raw = f.read()
    print("Первые 100 символов:", raw[:100])
    data = json.loads(raw)

# Авторизация
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(data, scope)
client = gspread.authorize(creds)

# Google Таблица
SHEET_ID = "1Z-m7fQwpU2_YJ8-HG4AuzSKHt_AD9eZ9D4uXlDH3flc"
sheet = client.open_by_key(SHEET_ID).sheet1

# Сохранение данных заказа
def save_order_data(order_data):
    try:
        booking_start = order_data.get("booking_start", "")
        booking_end = order_data.get("booking_end", "")

        if order_data.get("wants_preferred_type") and order_data.get("vehicle_type") != order_data.get("wants_preferred_type"):
            print(f"Предпочтительный ТС ({order_data['wants_preferred_type']}) занят. Выбран другой: {order_data['vehicle_type']}")

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
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            order_data.get("route_from", ""),
            order_data.get("route_to", ""),
            order_data.get("wants_preferred_type", ""),
            order_data.get("contact", "")
        ]
        sheet.append_row(row)
        print("Заказ успешно добавлен в Google Таблицу")
    except Exception as e:
        print(f"Ошибка при сохранении заказа: {str(e)}")
        raise

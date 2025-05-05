import os
import pandas as pd
from datetime import datetime

# Абсолютный путь до корня проекта
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
ORDERS_FILE = os.path.join(PROJECT_ROOT, 'outputs/web_orders_history.xlsx')

def save_web_order_data(order_data):
    os.makedirs(os.path.dirname(ORDERS_FILE), exist_ok=True)
    order_data['ДатаСоздания'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_order_df = pd.DataFrame([order_data])

    if os.path.exists(ORDERS_FILE):
        existing_df = pd.read_excel(ORDERS_FILE)
        updated_df = pd.concat([existing_df, new_order_df], ignore_index=True)
    else:
        updated_df = new_order_df

    updated_df.to_excel(ORDERS_FILE, index=False)

    print("=== Сохранение нового заказа ===")
    print("Данные:", order_data)
    print("Файл сохранения:", ORDERS_FILE)
    print("Успешно сохранено.")
    return True

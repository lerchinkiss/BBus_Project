import pandas as pd
import os
from datetime import datetime

ORDERS_FILE = "outputs/web_orders_history.xlsx"

def save_web_order_data(order_data):
    """
    Сохраняет данные заказа из веб-приложения в Excel файл
    order_data: dict - данные заказа
    """
    # Создаем директорию, если её нет
    os.makedirs(os.path.dirname(ORDERS_FILE), exist_ok=True)
    
    # Добавляем дату создания заказа
    order_data['ДатаСоздания'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Создаем DataFrame из данных заказа
    new_order_df = pd.DataFrame([order_data])
    
    # Если файл существует, читаем его и добавляем новые данные
    if os.path.exists(ORDERS_FILE):
        existing_df = pd.read_excel(ORDERS_FILE)
        updated_df = pd.concat([existing_df, new_order_df], ignore_index=True)
    else:
        updated_df = new_order_df
    
    # Сохраняем обновленный DataFrame
    updated_df.to_excel(ORDERS_FILE, index=False)
    return True 
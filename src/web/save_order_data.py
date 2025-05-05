import pandas as pd
import os
from datetime import datetime

# Абсолютный путь до файла истории заказов
ORDERS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outputs', 'web_orders_history.xlsx'))

def save_web_order_data(order_data):
    """
    Сохраняет данные заказа из веб-приложения в Excel файл
    order_data: dict - данные заказа
    """
    try:
        # Добавляем дату создания заказа
        order_data['ДатаСоздания'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Лог: выводим что пришло и куда хотим сохранить
        print("\n=== Сохранение нового заказа ===")
        print("Данные заказа:", order_data)
        print("Путь сохранения файла:", ORDERS_FILE)

        # Создаем директорию, если её нет
        os.makedirs(os.path.dirname(ORDERS_FILE), exist_ok=True)

        # Создаем DataFrame из одного заказа
        new_order_df = pd.DataFrame([order_data])

        # Если файл уже существует — загружаем и объединяем
        if os.path.exists(ORDERS_FILE):
            existing_df = pd.read_excel(ORDERS_FILE)
            updated_df = pd.concat([existing_df, new_order_df], ignore_index=True)
        else:
            updated_df = new_order_df

        # Сохраняем
        updated_df.to_excel(ORDERS_FILE, index=False)
        print("Заказ успешно сохранён.")

        return True
    except Exception as e:
        print("Ошибка при сохранении заказа:", str(e))
        raise

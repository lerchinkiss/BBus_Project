import sys
import os
import pandas as pd
# Добавить корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from link_tables import apply_links

# Определяем абсолютные пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PREPARED_DATA_DIR = os.path.join(DATA_DIR, "prepared_data")

# === Шаг 2: Подготовка обучающего набора ===
print("\nЗагрузка данных заказов...")
orders_df = pd.read_excel(os.path.join(DATA_DIR, "filtered_datasets", "bbOrders_filtered.xlsx"))
orders_df = apply_links(orders_df)

# Загрузка подготовленного профиля заказчиков
print("Загрузка профиля заказчиков...")
customer_profile = pd.read_excel(os.path.join(PREPARED_DATA_DIR, "customer_profile.xlsx"))

# Объединение заказов с профилем заказчиков
print("Объединение заказов с профилем...")
full_df = orders_df.merge(customer_profile, on='Заказчик', how='left')

# Если заказчик новый (нет профиля) — заполняем "Неизвестно"
for col in ['ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа']:
    full_df[col] = full_df[col].fillna('Неизвестно')

# Оставляем только нужные признаки для обучения
features = [
    'Заказчик',
    'КоличествоПассажиров',
    'ЦенаЗаЧас',
    'ТипЗаказа',
    'ЛюбимыйТипТС',
    'ИсторическийЛюбимыйТС',
    'ЛюбимыйСтатусЗаказа'
]
target = 'ТипТС'

full_df = full_df.dropna(subset=[target, 'КоличествоПассажиров', 'ЦенаЗаЧас', 'ТипЗаказа'])
X = full_df[features]
y = full_df[target]

# Сохраняем подготовленные данные
print("\nСохранение подготовленного набора данных...")
os.makedirs(PREPARED_DATA_DIR, exist_ok=True)
X.to_excel(os.path.join(PREPARED_DATA_DIR, "X_train_ready.xlsx"), index=False)
y.to_excel(os.path.join(PREPARED_DATA_DIR, "y_train_ready.xlsx"), index=False)

print("\n Данные для обучения сохранены в prepared_data/X_train_ready.xlsx и y_train_ready.xlsx")

import pandas as pd
import os
from link_tables import apply_links

# === Шаг 2: Подготовка обучающего набора ===
print("\nЗагрузка данных заказов...")
orders_df = pd.read_excel(os.path.join("filtered_datasets", "bbOrders_filtered.xlsx"))
orders_df = apply_links(orders_df)

# Загрузка подготовленного профиля заказчиков
print("Загрузка профиля заказчиков...")
customer_profile = pd.read_excel(os.path.join("prepared_data", "customer_profile.xlsx"))

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
os.makedirs("prepared_data", exist_ok=True)
X.to_excel(os.path.join("prepared_data", "X_train_ready.xlsx"), index=False)
y.to_excel(os.path.join("prepared_data", "y_train_ready.xlsx"), index=False)

print("\n✅ Данные для обучения сохранены в prepared_data/X_train_ready.xlsx и y_train_ready.xlsx")

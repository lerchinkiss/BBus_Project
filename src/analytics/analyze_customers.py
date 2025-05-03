import sys
import os

# Добавляем путь к корню проекта (где link_tables.py)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from app.link_tables import apply_links

# === Загрузка данных ===
df_path = os.path.join("../..", "filtered_datasets", "bbOrders_filtered.xlsx")
df = pd.read_excel(df_path)
df = apply_links(df)

# === Предобработка ===
df = df[df['Заказчик'].notna()]
df['Дата'] = pd.to_datetime(df['Date'], errors='coerce')
df['Маршрут'] = df['ЗагрузкаПункт'].astype(str) + " → " + df['РазгрузкаПункт'].astype(str)

# === Анализ: частота маршрутов на одного заказчика ===
print("\n--- Топ маршрутов по каждому заказчику ---")
top_routes_per_customer = (
    df.groupby(['Заказчик', 'Маршрут'])
    .size()
    .reset_index(name='Количество')
    .sort_values(['Заказчик', 'Количество'], ascending=[True, False])
)

# Для каждого заказчика — топ 1 маршрут
most_common_routes = top_routes_per_customer.groupby('Заказчик').first().reset_index()
print(most_common_routes.head(10))

# === Анализ: популярные ТС у каждого заказчика ===
print("\n--- Популярные ТС у заказчиков ---")
top_ts_per_customer = (
    df.groupby(['Заказчик', 'ТС'])
    .size()
    .reset_index(name='Частота')
    .sort_values(['Заказчик', 'Частота'], ascending=[True, False])
)

most_common_ts = top_ts_per_customer.groupby('Заказчик').first().reset_index()
print(most_common_ts.head(10))

# === Анализ: среднее число пассажиров у заказчиков ===
print("\n--- Среднее количество пассажиров ---")
df['КоличествоПассажиров'] = pd.to_numeric(df['КоличествоПассажиров'], errors='coerce')
avg_passengers = df.groupby('Заказчик')['КоличествоПассажиров'].mean().round(1)
print(avg_passengers.head(10))

# === Визуализация: распределение количества пассажиров ===
plt.figure(figsize=(10, 4))
sns.histplot(df['КоличествоПассажиров'].dropna(), bins=30, kde=True)
plt.title("Распределение количества пассажиров")
plt.xlabel("Пассажиров")
plt.tight_layout()
plt.show()

# === Сводка профилей заказчиков ===
profiles = df.groupby('Заказчик').agg({
    'КоличествоПассажиров': 'mean',
    'Маршрут': pd.Series.mode,
    'ТС': pd.Series.mode,
    'ТипТС': pd.Series.mode,
    'Дата': ['min', 'max', 'count']
})

profiles.columns = ['СреднееПассажиров', 'Маршрут', 'ТС', 'ТипТС', 'ПервыйЗаказ', 'ПоследнийЗаказ', 'ВсегоЗаказов']
profiles = profiles.reset_index()

print("\n📋 Пример сводки профиля клиента:")
print(profiles.head(3))

# === Сохранение профилей (если нужно) ===
os.makedirs("../../bbrecommend/bbrecommend", exist_ok=True)
profiles.to_excel("bbrecommend/customer_profiles.xlsx", index=False)

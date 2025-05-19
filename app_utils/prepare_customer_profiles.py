import pandas as pd
import os
from link_tables import apply_links

# === Загрузка данных ===
print("\nЗагрузка данных...")
df = pd.read_excel(os.path.join("../data/filtered_datasets", "bbOrders_filtered.xlsx"))

# Применяем раскодировку
print("Применение раскодировок...")
df = apply_links(df)

# Убираем пустых заказчиков
df = df[df['Заказчик'].notna()]

# === Построение профиля заказчиков ===
print("\nПостроение профиля заказчиков...")

# Функция для безопасного получения моды (самого частого значения)
def safe_mode(series):
    if not series.mode().empty:
        return series.mode().iloc[0]
    else:
        return 'Неизвестно'

# Группируем по заказчику и находим любимые значения
customer_profile = df.groupby('Заказчик').agg({
    'ТипТС': safe_mode,
    'ТС': safe_mode,
    'СтатусЗаказа': safe_mode
}).reset_index()

customer_profile.columns = ['Заказчик', 'ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа']

print("\nПервые строки профиля заказчиков:")
print(customer_profile.head())

# === Сохранение профиля ===
print("\nСохранение профиля заказчиков...")
os.makedirs("../data/prepared_data", exist_ok=True)
customer_profile.to_excel(os.path.join("../data/prepared_data", "customer_profile.xlsx"), index=False)

print("\nПрофиль заказчиков сохранён в prepared_data/customer_profile.xlsx")

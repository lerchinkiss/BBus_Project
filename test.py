import pandas as pd
from link_tables import apply_links

# Загружаем файл
df = pd.read_excel("data/filtered_datasets/bbOrders_filtered.xlsx")
df = apply_links(df)

# Группируем по ТС и считаем среднюю стоимость
avg_prices = df.groupby("ТипТС")["ЦенаЗаЧас"].mean().round().astype(int)

# Сортируем по названию
avg_prices = avg_prices.sort_index()

# Формируем строки для HTML tooltip
tooltip_lines = [f"{ts} – {price} руб." for ts, price in avg_prices.items()]
tooltip_text = "Средняя стоимость ТС в час:\n" + "\n".join(tooltip_lines)

# Выводим результат
print(tooltip_text)

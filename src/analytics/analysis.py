import pandas as pd

# Загрузка данных
orders_df = pd.read_excel('data/filtered_datasets/bbOrders_filtered.xlsx')
types_df = pd.read_excel('data/filtered_datasets/uatTypeTS_filtered.xlsx')

# Объединение по ключу "ТипТС" из orders_df и "Ref" из types_df
merged_df = orders_df.merge(types_df[['Ref', 'Description']], left_on='ТипТС', right_on='Ref', how='left')

# Группировка по названию типа ТС и агрегация
result = merged_df.groupby('Description')['ЦенаЗаЧас'].agg(['min', 'max']).reset_index()

# Переименование столбцов для ясности
result.columns = ['Тип ТС', 'Минимальная цена за час', 'Максимальная цена за час']

# Вывод результата
print(result)

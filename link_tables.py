import os
import pandas as pd

# Словарь: колонка в bbOrders → (имя файла, колонка для связи)
filtered_path = 'filtered_datasets'
raw_path = 'datasets'

# Загружаем основной датафрейм
orders_path = os.path.join(filtered_path, 'bbOrders_filtered.xlsx')
bbOrders = pd.read_excel(orders_path)

# Словарь: колонка в bbOrders → (имя файла, Ref-колонка)
reference_mapping = {
    'Заказчик': ('contragents_filtered', 'Ref'),
    'ТС': ('uatTS_filtered', 'Ref'),
    'КонтактноеЛицо': ('PartnerContacts_filtered', 'Ref'),
    'Организация': ('Organizations_filtered', 'Ref'),
    'Ответсвенный': ('Users_filtered', 'Ref'),
    'ТипТС': ('uatTypeTS_filtered', 'Ref'),
    'Тариф': ('bbTariffs_filtered', 'Ref'),
    'Водитель': ('uatWorkers_filtered', 'Ref'),
    'Создатель': ('Users_filtered', 'Ref'),
    'Водитель2': ('uatWorkers_filtered', 'Ref'),
    'ТипЗаказа': ('bbOrderTypes', 'Ref'),
    'СтатусЗаказа': ('bbStatus', 'Ref')
}

# Подстановка в памяти
for col, (filename, ref_col) in reference_mapping.items():
    # Пробуем найти файл в filtered_datasets, иначе в datasets
    filepath = os.path.join(filtered_path, f'{filename}.xlsx')
    if not os.path.exists(filepath):
        filepath = os.path.join(raw_path, f'{filename}.xlsx')
        if not os.path.exists(filepath):
            print(f"Файл {filename}.xlsx не найден ни в filtered_datasets, ни в datasets")
            continue

    # Загружаем связанный датасет
    ref_df = pd.read_excel(filepath)
    #Если колонки нет в датафрейме, также выпишем какие есть
    if ref_col not in ref_df.columns:
        print(f"В таблице {filename}.xlsx нет колонки '{ref_col}'!")
        print(f"Найденные колонки: {list(ref_df.columns)}")
        continue

    value_cols = [c for c in ref_df.columns if c != ref_col]
    if not value_cols:
        print(f"Нет подходящей колонки для отображения в {filename}")
        continue

    display_col = value_cols[0]
    mapping = dict(zip(ref_df[ref_col], ref_df[display_col]))
    bbOrders[col] = bbOrders[col].map(mapping).fillna(bbOrders[col])
    print(f"{col} → {filename}.{display_col} (заменено по ссылке)")




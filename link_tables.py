import os
import pandas as pd

# Текущий путь до этого файла
BASE_DIR = os.path.dirname(__file__)
filtered_path = os.path.join(BASE_DIR, 'filtered_datasets')
raw_path = os.path.join(BASE_DIR, 'datasets')

# Загружаем основной датафрейм
orders_path = os.path.join(filtered_path, 'bbOrders_filtered.xlsx')
bbOrders = pd.read_excel(orders_path)

def apply_links(bbOrders, filtered_path=filtered_path, raw_path=raw_path):
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

    for col, (filename, ref_col) in reference_mapping.items():
        filepath = os.path.join(filtered_path, f'{filename}.xlsx')
        if not os.path.exists(filepath):
            filepath = os.path.join(raw_path, f'{filename}.xlsx')
            if not os.path.exists(filepath):
                print(f"Файл {filename}.xlsx не найден")
                continue

        ref_df = pd.read_excel(filepath)

        if ref_col not in ref_df.columns:
            print(f"Нет колонки '{ref_col}' в {filename}")
            continue

        if 'Description' not in ref_df.columns:
            print(f"Нет колонки 'Description' в {filename}")
            continue

        mapping = dict(zip(ref_df[ref_col], ref_df['Description']))
        bbOrders[col] = bbOrders[col].map(mapping).fillna(bbOrders[col])
        print(f"{col} → {filename}.Description")

    return bbOrders

import streamlit as st
st.set_page_config(page_title="Предсказание типа ТС", layout="centered")

import os
import pandas as pd
from catboost import CatBoostClassifier, Pool

# === Загрузка модели ===
model_path = "catboost_typeTS_model.cbm"
model = CatBoostClassifier()
model.load_model(model_path)

# === Загрузка примеров значений из данных ===
@st.cache_data
@st.cache_data
def get_options():
    def load_desc(file_name):
        for folder in ["filtered_datasets", "datasets"]:
            path = os.path.join(folder, file_name)
            if os.path.exists(path):
                df = pd.read_excel(path)
                return sorted(df['Description'].dropna().unique())
        raise FileNotFoundError(f"Файл {file_name} не найден ни в 'filtered_datasets/', ни в 'datasets/'")

    # Основной датасет с маршрутами
    for folder in ["filtered_datasets", "datasets"]:
        orders_path = os.path.join(folder, "bbOrders_filtered.xlsx")
        if os.path.exists(orders_path):
            orders = pd.read_excel(orders_path)
            break
    else:
        raise FileNotFoundError("Файл 'bbOrders_filtered.xlsx' не найден")

    orders['Маршрут'] = orders['ЗагрузкаПункт'].astype(str) + ' → ' + orders['РазгрузкаАдрес'].astype(str)

    return {
        'Заказчик': load_desc("contragents_filtered.xlsx"),
        'ТС': load_desc("uatTS_filtered.xlsx"),
        'Водитель': load_desc("uatWorkers_filtered.xlsx"),
        'Тариф': load_desc("bbTariffs_filtered.xlsx"),
        'ТипЗаказа': load_desc("bbOrderTypes.xlsx"),
        'Маршрут': sorted(orders['Маршрут'].dropna().unique())
    }


options = get_options()

# === Интерфейс ===
st.title("🚌 Рекомендованный Тип ТС")

with st.form("predict_form"):
    количество_пассажиров = st.number_input("Количество пассажиров", min_value=1, max_value=100, value=10)
    цена_за_час = st.number_input("Цена за час", min_value=500, max_value=10000, value=2500)
    фактическая_стоимость = st.number_input("Фактическая стоимость", min_value=500, max_value=500000, value=30000)

    заказчик = st.selectbox("Заказчик", options['Заказчик'])
    тс = st.selectbox("ТС", options['ТС'])
    водитель = st.selectbox("Водитель", options['Водитель'])
    тариф = st.selectbox("Тариф", options['Тариф'])
    тип_заказа = st.selectbox("Тип заказа", options['ТипЗаказа'])
    маршрут = st.selectbox("Маршрут", options['Маршрут'])

    submitted = st.form_submit_button("Предсказать")

# === Предсказание ===
if submitted:
    input_data = pd.DataFrame([{
        'КоличествоПассажиров': количество_пассажиров,
        'ЦенаЗаЧас': цена_за_час,
        'ФактическаяСтоимость': фактическая_стоимость,
        'Заказчик': заказчик,
        'ТС': тс,
        'Водитель': водитель,
        'Тариф': тариф,
        'ТипЗаказа': тип_заказа,
        'Маршрут': маршрут
    }])

    pool = Pool(input_data, cat_features=input_data.select_dtypes('object').columns.tolist())
    prediction = model.predict(pool)[0]

    st.success(f"🚍 Рекомендованный Тип ТС: **{prediction}**")

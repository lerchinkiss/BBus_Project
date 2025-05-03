import streamlit as st
import pandas as pd
import os
from catboost import CatBoostClassifier, Pool
from app.link_tables import apply_links

st.set_page_config(page_title="Рекомендация ТС", layout="centered")

# === Загрузка модели ===
model = CatBoostClassifier()
model.load_model("catboost_typets_model_v2.cbm")

# === Загрузка данных и раскодировка типов ТС ===
@st.cache_data

def load_reference_data():
    df = pd.read_excel(os.path.join("data/filtered_datasets", "bbOrders_filtered.xlsx"))
    df = apply_links(df)
    typets_list = df['ТипТС'].dropna().unique()
    typets_dict = {x: x for x in typets_list}
    return df, typets_dict

orders_df, typets_dict = load_reference_data()

# Получаем список уникальных заказчиков
unique_companies = sorted(orders_df['Заказчик'].dropna().unique())

# === Интерфейс Streamlit ===
st.title("Рекомендация типа транспортного средства")

st.markdown("Заполните информацию о заказе:")

with st.form("order_form"):
    заказчик = st.selectbox("Выберите заказчика или введите нового:", unique_companies + ["Новый заказчик"])
    if заказчик == "Новый заказчик":
        заказчик = st.text_input("Введите название новой компании:", "Компания ХХХ")

    количество_пассажиров = st.number_input("Количество пассажиров:", min_value=1, max_value=100, value=10)
    цена_за_час = st.number_input("Стоимость за час аренды (руб.):", min_value=500, max_value=10000, value=2500)
    тип_заказа = st.selectbox("Тип заказа:", ["Стандарт", "Свадьба", "Дети"])

    submitted = st.form_submit_button("Рекомендовать транспорт")

# === Предсказание ===
if submitted:
    input_data = pd.DataFrame([{
        'Заказчик': заказчик,
        'КоличествоПассажиров': количество_пассажиров,
        'ЦенаЗаЧас': цена_за_час,
        'ТипЗаказа': тип_заказа
    }])

    pool = Pool(input_data, cat_features=['Заказчик', 'ТипЗаказа'])

    # Предсказание вероятностей
    probs = model.predict_proba(pool)[0]
    top_indices = probs.argsort()[-3:][::-1]

    st.subheader("Топ-3 рекомендованных типа ТС:")
    for idx in top_indices:
        ref = model.classes_[idx]
        description = typets_dict.get(ref, ref)
        probability = probs[idx]
        st.write(f"{description} — вероятность: {probability:.2%}")

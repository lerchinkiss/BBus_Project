import streamlit as st
import pandas as pd
import os
from catboost import CatBoostClassifier, Pool
from link_tables import apply_links

st.set_page_config(page_title="Рекомендация транспортного средства", layout="centered")

# === Загрузка модели ===
model = CatBoostClassifier()
model.load_model(os.path.join("models", "catboost_typets_model_v3.cbm"))


# === Загрузка данных ===
@st.cache_data
def load_data():
    orders_df = pd.read_excel(os.path.join("filtered_datasets", "bbOrders_filtered.xlsx"))
    orders_df = apply_links(orders_df)
    customer_profile = pd.read_excel(os.path.join("prepared_data", "customer_profile.xlsx"))
    # Загрузка вместимости типов ТС
    type_ts_df = pd.read_excel(os.path.join("filtered_datasets", "uatTypeTS_filtered.xlsx"))
    type_ts_df = type_ts_df.dropna(subset=['Description', 'МаксМест'])
    type_ts_mapping = dict(zip(type_ts_df['Description'], type_ts_df['МаксМест']))
    return orders_df, customer_profile, type_ts_mapping


orders_df, customer_profile, type_ts_mapping = load_data()

# Список заказчиков
unique_companies = sorted(orders_df['Заказчик'].dropna().unique())

# === Интерфейс Streamlit ===
st.title("Рекомендация типа транспортного средства")

st.markdown("Заполните информацию о заказе:")

with st.form("order_form"):
    заказчик = st.selectbox("Выберите заказчика или введите нового:", unique_companies + ["Новый заказчик"])
    if заказчик == "Новый заказчик":
        заказчик = st.text_input("Введите название новой компании:", "Компания ХХХ")

    количество_пассажиров = st.number_input("Количество пассажиров:", min_value=1, max_value=59, value=10)
    цена_за_час = st.number_input("Стоимость за час аренды (руб.):", min_value=500, max_value=10000, value=2500)
    тип_заказа = st.selectbox("Тип заказа:", ["Стандарт", "Свадьба", "Дети"])

    submitted = st.form_submit_button("Рекомендовать транспорт")

# === Логика предсказания ===
if заказчик and заказчик != "Новый заказчик":
    st.markdown("---")
    st.subheader("Профиль заказчика")
    profile_row = customer_profile[customer_profile['Заказчик'] == заказчик]

    if not profile_row.empty:
        любимый_тип_тс = profile_row['ЛюбимыйТипТС'].values[0]
        исторический_любимый_тс = profile_row['ИсторическийЛюбимыйТС'].values[0]
        любимый_статус_заказа = profile_row['ЛюбимыйСтатусЗаказа'].values[0]

        среднее_пассажиров = orders_df[orders_df['Заказчик'] == заказчик]['КоличествоПассажиров'].mean()
        всего_заказов = orders_df[orders_df['Заказчик'] == заказчик].shape[0]

        st.write(f"**Любимый тип ТС:** {любимый_тип_тс}")
        st.write(f"**Любимая модель ТС:** {исторический_любимый_тс}")
        st.write(f"**Любимый статус заказа:** {любимый_статус_заказа}")
        st.write(f"**Среднее количество пассажиров:** {среднее_пассажиров:.1f}")
        st.write(f"**Всего заказов:** {всего_заказов}")
    else:
        st.info("Нет данных по заказчику.")

# === Предсказание ===
if submitted:
    # Подтягиваем профиль заказчика
    profile_row = customer_profile[customer_profile['Заказчик'] == заказчик]

    if not profile_row.empty:
        любимый_тип_тс = profile_row['ЛюбимыйТипТС'].values[0]
        исторический_любимый_тс = profile_row['ИсторическийЛюбимыйТС'].values[0]
        любимый_статус_заказа = profile_row['ЛюбимыйСтатусЗаказа'].values[0]
    else:
        любимый_тип_тс = 'Неизвестно'
        исторический_любимый_тс = 'Неизвестно'
        любимый_статус_заказа = 'Неизвестно'

    # Формируем датафрейм для предсказания
    input_data = pd.DataFrame([{
        'Заказчик': заказчик,
        'КоличествоПассажиров': количество_пассажиров,
        'ЦенаЗаЧас': цена_за_час,
        'ТипЗаказа': тип_заказа,
        'ЛюбимыйТипТС': любимый_тип_тс,
        'ИсторическийЛюбимыйТС': исторический_любимый_тс,
        'ЛюбимыйСтатусЗаказа': любимый_статус_заказа
    }])

    # Определяем категориальные признаки
    pool = Pool(input_data,
                cat_features=['Заказчик', 'ТипЗаказа', 'ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа'])

    # Предсказание вероятностей
    probs = model.predict_proba(pool)[0]
    top_indices = probs.argsort()[-10:][::-1]  # Берем топ-10, чтобы фильтровать


    # Диапазоны вместимости
    def define_range(passengers):
        if passengers <= 4:
            return (1, 4)
        elif passengers <= 8:
            return (5, 8)
        elif passengers <= 20:
            return (9, 20)
        elif passengers <= 50:
            return (21, 50)
        else:
            return (51, 100)


    min_capacity, max_capacity = define_range(количество_пассажиров)

    recommendations = []

    for idx in top_indices:
        ref = model.classes_[idx]
        probability = probs[idx]
        capacity = type_ts_mapping.get(ref, 999)

        if min_capacity <= capacity <= max_capacity:
            recommendations.append((ref, probability, capacity))

        if len(recommendations) == 3:
            break

    # Параллельно ищем в истории заказов
    historical_matches = orders_df[
        (orders_df['КоличествоПассажиров'] >= min_capacity) & (orders_df['КоличествоПассажиров'] <= max_capacity)]
    if not historical_matches.empty:
        top_historical = historical_matches['ТипТС'].value_counts().head(3).index.tolist()
        for ref in top_historical:
            if all(r[0] != ref for r in recommendations):
                capacity = type_ts_mapping.get(ref, 999)
                recommendations.append((ref, 0.0, capacity))
                if len(recommendations) == 3:
                    break

    st.markdown("---")
    st.subheader("Топ-3 рекомендованных типа ТС:")
    for ref, probability, capacity in recommendations:
        st.write(f"{ref} (вместимость: {int(capacity)} мест) — вероятность: {probability:.2%}")

    if not recommendations:
        st.warning("Не удалось найти подходящий транспорт по количеству пассажиров.")

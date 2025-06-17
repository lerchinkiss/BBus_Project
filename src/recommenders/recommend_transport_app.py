import streamlit as st
from link_tables import apply_links
from common_imports import *
from testapp_saveorder import save_order_data

# Настройка страницы
st.set_page_config(
    page_title="Рекомендация транспортного средства",
    page_icon="🚌",
    layout="centered"
)

# === Загрузка модели ===
@st.cache_resource
def load_model():
    model = CatBoostClassifier()
    model.load_model(os.path.join(MODELS_DIR, "catboost_typets_model_v3.cbm"))
    return model

model = load_model()

# === Загрузка данных ===
@st.cache_data
def load_data():
    # Загрузка данных заказов
    orders_df = pd.read_excel(os.path.join(DATA_DIR, "filtered_datasets", "bbOrders_filtered.xlsx"))
    orders_df = apply_links(orders_df)
    
    # Загрузка профиля заказчиков
    customer_profile = pd.read_excel(os.path.join(PREPARED_DATA_DIR, "customer_profile.xlsx"))
    
    # Загрузка информации о типах ТС
    type_ts_df = pd.read_excel(os.path.join(DATA_DIR, "filtered_datasets", "uatTypeTS_filtered.xlsx"))
    type_ts_df = type_ts_df.dropna(subset=['Description', 'МаксМест'])
    type_ts_mapping = dict(zip(type_ts_df['Description'], type_ts_df['МаксМест']))
    
    return orders_df, customer_profile, type_ts_mapping

orders_df, customer_profile, type_ts_mapping = load_data()

# === Интерфейс ===
st.title("🚌 Рекомендация типа транспортного средства")

# Список заказчиков
unique_companies = sorted(orders_df['Заказчик'].dropna().unique())

# Форма ввода данных
with st.form("order_form"):
    st.markdown("### 📝 Информация о заказе")
    
    col1, col2 = st.columns(2)
    with col1:
        заказчик = st.selectbox("Выберите заказчика:", unique_companies + ["Новый заказчик"])
        if заказчик == "Новый заказчик":
            заказчик = st.text_input("Введите название новой компании:", key="new_company")
            if not заказчик:
                st.warning("Пожалуйста, введите название компании")
                st.stop()
        
        количество_пассажиров = st.number_input(
            "Количество пассажиров:",
            min_value=1,
            max_value=59,
            value=10,
            help="Укажите планируемое количество пассажиров"
        )
    
    with col2:
        цена_за_час = st.number_input(
            "Стоимость за час аренды (руб.):",
            min_value=500,
            max_value=10000,
            value=2500,
            help="Укажите бюджет на час аренды"
        )
        
        тип_заказа = st.selectbox(
            "Тип заказа:",
            ["Стандарт", "Свадьба", "Дети"],
            help="Выберите тип заказа"
        )
    
    submitted = st.form_submit_button("Получить рекомендации")

# === Отображение профиля заказчика ===
if заказчик and заказчик != "Новый заказчик":
    st.markdown("---")
    st.subheader("👤 Профиль заказчика")
    profile_row = customer_profile[customer_profile['Заказчик'] == заказчик]
    
    if not profile_row.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Любимый тип ТС", profile_row['ЛюбимыйТипТС'].values[0])
            st.metric("Любимая модель ТС", profile_row['ИсторическийЛюбимыйТС'].values[0])
        with col2:
            st.metric("Любимый статус заказа", profile_row['ЛюбимыйСтатусЗаказа'].values[0])
            st.metric("Среднее количество пассажиров", 
                     f"{orders_df[orders_df['Заказчик'] == заказчик]['КоличествоПассажиров'].mean():.1f}")
    else:
        st.info("ℹ️ Нет данных по заказчику.")

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
        'КоличествоПассажиров': количество_пассажиров,
        'ЦенаЗаЧас': цена_за_час,
        'ФактическаяСтоимость': цена_за_час,
        'Заказчик': заказчик,
        'ТипЗаказа': тип_заказа,
        'ЛюбимыйТипТС': любимый_тип_тс,
        'ИсторическийЛюбимыйТС': исторический_любимый_тс,
        'ЛюбимыйСтатусЗаказа': любимый_статус_заказа
    }])
    
    # Сохраняем данные заказа
    order_data = {
        'Заказчик': заказчик,
        'КоличествоПассажиров': количество_пассажиров,
        'ЦенаЗаЧас': цена_за_час,
        'ТипЗаказа': тип_заказа,
        'ЛюбимыйТипТС': любимый_тип_тс,
        'ИсторическийЛюбимыйТС': исторический_любимый_тс,
        'ЛюбимыйСтатусЗаказа': любимый_статус_заказа
    }
    
    if save_order_data(order_data):
        st.success("✅ Данные заказа сохранены")
    
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
        (orders_df['КоличествоПассажиров'] >= min_capacity) & 
        (orders_df['КоличествоПассажиров'] <= max_capacity)
    ]
    
    if not historical_matches.empty:
        top_historical = historical_matches['ТипТС'].value_counts().head(3).index.tolist()
        for ref in top_historical:
            if all(r[0] != ref for r in recommendations):
                capacity = type_ts_mapping.get(ref, 999)
                recommendations.append((ref, 0.0, capacity))
                if len(recommendations) == 3:
                    break
    
    # Отображение результатов
    st.markdown("---")
    st.subheader("🚍 Рекомендованные типы ТС")
    
    if recommendations:
        for i, (ref, probability, capacity) in enumerate(recommendations, 1):
            with st.expander(f"{i}. {ref} (вместимость: {int(capacity)} мест)"):
                st.metric("Вероятность", f"{probability:.2%}")
                st.metric("Вместимость", f"{int(capacity)} мест")
                
                # Показываем историю использования
                historical_usage = orders_df[orders_df['ТипТС'] == ref]
                if not historical_usage.empty:
                    st.markdown("#### 📊 История использования")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Всего заказов", len(historical_usage))
                        st.metric("Среднее количество пассажиров", 
                                 f"{historical_usage['КоличествоПассажиров'].mean():.1f}")
                    with col2:
                        st.metric("Средняя стоимость заказа", 
                                 f"{historical_usage['ФактическаяСтоимость'].mean():,.0f} руб.")
                        st.metric("Средняя стоимость за час", 
                                 f"{historical_usage['ЦенаЗаЧас'].mean():,.0f} руб.")
    else:
        st.warning("⚠️ Не удалось найти подходящий транспорт по количеству пассажиров.")

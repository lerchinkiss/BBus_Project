import pandas as pd
import os
import streamlit as st

file_path = os.path.join("datasets", "generated_orders_upgrade.csv")

# Загрузка данных
try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    st.error("Файл не найден. Проверьте путь к файлу.")
    st.stop()

# Преобразуем даты и время
for col in ['время_начала', 'время_окончания']:
    df[col] = pd.to_datetime(df[col])

df['длительность_поездки'] = (df['время_окончания'] - df['время_начала']).dt.total_seconds() / 3600  # В часах

# Заголовок веб-приложения
st.title("АНАЛИЗ БРОНИ ТРАНСПОРТОВ")

st.header("📊 Общая статистика")

# Самый популярное авто
bus_popularity = df['bus_id'].value_counts()
most_popular_bus = bus_popularity.idxmax()
most_popular_bus_count = bus_popularity.max()
st.write(f"**Самый популярный трнаспорт:** {most_popular_bus} (бронировали {most_popular_bus_count} раз)")

# Средняя длительность поездки
avg_booking_time = df['длительность_поездки'].mean()
st.write(f"**Средняя длительность поездки:** {avg_booking_time:.2f} часов")

# Самый популярный статус оплаты
payment_status_counts = df['статус_оплаты'].value_counts()
most_common_payment_status = payment_status_counts.idxmax()
st.write(f"**Самый популярный статус оплаты:** {most_common_payment_status}")

# Самое популярное направление
most_popular_end_location = df['end_location'].value_counts().idxmax()
st.write(f"**Самое популярное направление:** {most_popular_end_location}")

# День недели с наибольшим числом бронирований
df['день_недели'] = df['дата_заказа'].astype(str).apply(lambda x: pd.to_datetime(x).day_name())
most_popular_day = df['день_недели'].value_counts().idxmax()
st.write(f"**День недели с наибольшим числом бронирований:** {most_popular_day}")

# Анализ пассажиров
st.header("🚏 Пассажиры и транспорты")

# Среднее количество пассажиров по типам автобусов
avg_passengers_by_bus_type = df.groupby('bus_type')['количество_пассажиров'].mean()
st.write("**Среднее количество пассажиров по типам транспортов:**")
st.dataframe(avg_passengers_by_bus_type)

# --- Фильтр по клиенту ---
st.header("🔍 Анализ поездок конкретного клиента")

# Выбор клиента
unique_clients = df['client_id'].unique()
selected_client = st.selectbox("Выберите клиента:", unique_clients)

# Вывод поездок клиента
client_trips = df[df['client_id'] == selected_client]
st.write(f"Поездки клиента **{selected_client}**")
st.dataframe(client_trips)

# Визуализация
st.header("📈 Графики")

# График частоты бронирования автобусов
st.bar_chart(bus_popularity)

# График частоты способов оплаты
st.bar_chart(payment_status_counts)

# График количества бронирований по дням недели
day_counts = df['день_недели'].value_counts()
st.bar_chart(day_counts)




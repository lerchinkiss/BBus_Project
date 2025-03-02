import random
import pandas as pd
from faker import Faker

fake = Faker("ru_RU")

num_clients = 500
num_rows = 2000  # Количество заказов

moscow_streets_path = "moscow.csv"
moscow_streets_df = pd.read_csv(moscow_streets_path)
moscow_streets = moscow_streets_df['улица'].dropna().tolist()

bus_details_path = "datasets/bus_details.csv"
bus_details_df = pd.read_csv(bus_details_path)

# Соответствие типов автобусов
bus_details_df["bus_type"] = bus_details_df["Услуга"].map({
    "аренда автобуса": "автобус",
    "аренда микроавтобуса": "микроавтобус",
    "аренда минивэна": "минивэн",
    "аренда авто": "авто"
})

bus_ids = list(range(1, 42))  # ID автобусов от 1 до 41

def generate_address():
    street = random.choice(moscow_streets)
    house_number = random.randint(1, 150)
    return f"Москва, {street}, {house_number}"

driver_names = [fake.name() for _ in range(200)]

# Возможные комментарии
comments_list = [
    "Требуется детское кресло", "Нужен англоговорящий водитель", "Персональная встреча с табличкой",
    "Дополнительный багажный отсек", "", "", "", "", "Оплата наличными по приезду", ""
]

client_orders = []
for client_id in range(1, num_clients + 1):
    num_orders = random.randint(1, 4)
    client_orders.extend([client_id] * num_orders)

random.shuffle(client_orders)
if len(client_orders) > num_rows:
    client_orders = client_orders[:num_rows]
elif len(client_orders) < num_rows:
    client_orders.extend(random.choices(client_orders, k=num_rows - len(client_orders)))


def parse_capacity(value):
    if isinstance(value, str) and "/" in value:
        return max(map(int, value.split("/")))
    try:
        return int(value)
    except ValueError:
        return 50

bus_details_df["Вместимость"] = bus_details_df["Вместимость"].apply(parse_capacity)

data_fixed = []
for i, client_id in enumerate(client_orders):
    order_date = fake.date_between_dates(date_start=pd.Timestamp(2025, 1, 1), date_end=pd.Timestamp(2025, 1, 31))
    trip_date = fake.date_between_dates(date_start=order_date, date_end=pd.Timestamp(2025, 1, 31))

    start_time_hour = random.randint(0, 23)
    start_time_minute = random.randint(0, 59)
    start_time = pd.Timestamp(trip_date).replace(hour=start_time_hour, minute=start_time_minute)

    duration_hours = random.randint(2, 72)
    end_time = start_time + pd.Timedelta(hours=duration_hours)

    start_location = generate_address()
    end_location = generate_address()

    distance_km = random.uniform(2, 50)

    # Количество пассажиров
    max_passengers = random.randint(1, 65)

    # Выбираем автобус с подходящей вместимостью
    suitable_buses = bus_details_df[bus_details_df["Вместимость"] >= max_passengers]

    if not suitable_buses.empty:
        selected_bus = suitable_buses.sample(1).iloc[0]
    else:
        selected_bus = bus_details_df.sample(1).iloc[0]

    bus_id = selected_bus.name % 41 + 1
    bus_type = selected_bus["bus_type"]
    max_capacity = selected_bus["Вместимость"]

    driver_name = random.choice(driver_names)
    comments = random.choice(comments_list)

    num_passengers = random.randint(1, max_capacity)  # Ограничиваем вместимостью автобуса

    data_fixed.append({
        "order_id": fake.uuid4(),
        "client_id": client_id,
        "дата_заказа": order_date,
        "время_начала": start_time.strftime("%Y-%m-%d %H:%M"),
        "время_окончания": end_time.strftime("%Y-%m-%d %H:%M"),
        "количество_пассажиров": num_passengers,
        "цель_поездки": random.choice([
            "Школьная экскурсия", "Свадьба", "Сопровождение из аэропорта",
            "Деловая поездка", "Туристическая экскурсия", "Корпоративное мероприятие",
            "Частная аренда", "Трансфер на вокзал"
        ]),
        "статус_оплаты": random.choice(["Оплачено", "Предоплата"]),
        "способ_оплаты": random.choice(["Наличные", "Карта"]),
        "start_location": start_location,
        "end_location": end_location,
        "distance_km": round(distance_km, 2),
        "bus_id": bus_id,
        "bus_type": bus_type,
        "driver_name": driver_name,
        "comments": comments
    })

df_fixed = pd.DataFrame(data_fixed)

assert len(df_fixed) == num_rows, f"Ошибка: получили {len(df_fixed)} строк вместо {num_rows}!"

output_path_fixed = "generated_orders.csv"
df_fixed.to_csv(output_path_fixed, index=False, encoding="utf-8-sig")

print(f"Файл сохранен: {output_path_fixed}, количество строк: {len(df_fixed)}")

import random
import pandas as pd
from faker import Faker

fake = Faker("ru_RU")

num_clients = 500
num_rows = 2000  # Количество заказов

client_orders = []
for client_id in range(1, num_clients + 1):
    num_orders = random.randint(1, 4)
    client_orders.extend([client_id] * num_orders)

random.shuffle(client_orders)
if len(client_orders) > num_rows:
    client_orders = client_orders[:num_rows]
elif len(client_orders) < num_rows:
    client_orders.extend(random.choices(client_orders, k=num_rows - len(client_orders)))

data_fixed = []
for client_id in client_orders:
    order_date = fake.date_between_dates(date_start=pd.Timestamp(2025, 1, 1), date_end=pd.Timestamp(2025, 1, 31))
    trip_date = fake.date_between_dates(date_start=order_date, date_end=pd.Timestamp(2025, 1, 31))

    start_time_hour = random.randint(0, 23)
    start_time_minute = random.randint(0, 59)
    start_time = pd.Timestamp(trip_date).replace(hour=start_time_hour, minute=start_time_minute)

    duration_hours = random.randint(2, 72)
    end_time = start_time + pd.Timedelta(hours=duration_hours)

    data_fixed.append({
        "order_id": fake.uuid4(),
        "client_id": client_id,
        "дата_заказа": order_date,
        "время_начала": start_time.strftime("%Y-%m-%d %H:%M"),  # Дата + время начала
        "время_окончания": end_time.strftime("%Y-%m-%d %H:%M"),  # Дата + время окончания
        "количество_пассажиров": random.randint(1, 50),
        "цель_поездки": random.choice([
            "Школьная экскурсия", "Свадьба", "Сопровождение из аэропорта",
            "Деловая поездка", "Туристическая экскурсия", "Корпоративное мероприятие",
            "Частная аренда", "Трансфер на вокзал"
        ]),
        "статус_оплаты": random.choice(["Оплачено", "Предоплата"]),
        "способ_оплаты": random.choice(["Наличные", "Карта"])
    })

df_fixed = pd.DataFrame(data_fixed)

assert len(df_fixed) == num_rows, f"Ошибка: получили {len(df_fixed)} строк вместо {num_rows}!"

output_path_fixed = "generated_orders.csv"
df_fixed.to_csv(output_path_fixed, index=False, encoding="utf-8-sig")

print(f"Файл сохранен: {output_path_fixed}, количество строк: {len(df_fixed)}")

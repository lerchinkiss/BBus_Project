import random
import pandas as pd
from faker import Faker

fake = Faker()

num_clients = 500
num_rows = 2000  # Количество заказов


def generate_orders():
    client_orders = []

    # Генерируем клиентов и распределяем им заказы
    while len(client_orders) < num_rows:
        client_id = random.randint(1, num_clients)
        if client_orders.count(client_id) < 4:
            client_orders.append(client_id)

    random.shuffle(client_orders)
    client_orders = client_orders[:num_rows]

    #Генерируем данные с условием order_date <= trip_date
    data_fixed = []
    for client_id in client_orders:
        order_date = fake.date_between_dates(date_start=pd.Timestamp(2025, 1, 1), date_end=pd.Timestamp(2025, 1, 31))
        trip_date = fake.date_between_dates(date_start=order_date, date_end=pd.Timestamp(2025, 1, 31))

        data_fixed.append({
            "order_id": fake.uuid4(),
            "client_id": client_id,
            "order_date": order_date,
            "trip_date": trip_date
        })

    return data_fixed

data_final = generate_orders()
if len(data_final) != num_rows:
    data_final = generate_orders()

df_fixed = pd.DataFrame(data_final)

output_path_fixed = "generated_orders.csv"
df_fixed.to_csv(output_path_fixed, index=False)

print(f"Файл сохранен: {output_path_fixed}, количество строк: {len(df_fixed)}")

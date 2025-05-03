import os
import sys
import pandas as pd
from sklearn.neighbors import NearestNeighbors

# Путь к проекту (укажем вручную)
BASE_DIR = "/"
sys.path.append(BASE_DIR)

from app.link_tables import apply_links

# Пути к данным
ORDERS_PATH = os.path.join(BASE_DIR, "../../data/filtered_datasets", "bbOrders_filtered.xlsx")

# Загрузка и обработка данных
df = pd.read_excel(ORDERS_PATH)
df = apply_links(df)

# Фильтрация нужных полей
df = df[['Заказчик', 'ТС', 'ТипТС', 'ЗагрузкаПункт', 'РазгрузкаАдрес']].dropna()
df['Маршрут'] = df['ЗагрузкаПункт'].astype(str) + " → " + df['РазгрузкаАдрес'].astype(str)
df = df[['Заказчик', 'ТС', 'Маршрут', 'ТипТС']]

# Матрица заказчик x ТС
user_ts_matrix = pd.crosstab(df['Заказчик'], df['ТС'])

# Обучение модели
model_knn = NearestNeighbors(metric='cosine', algorithm='brute')
model_knn.fit(user_ts_matrix.values)


# Рекомендации
def recommend_ts_for_customer(customer_name, top_n=5):
    if customer_name not in user_ts_matrix.index:
        return f"Заказчик '{customer_name}' отсутствует в истории заказов."

    customer_vector = user_ts_matrix.loc[customer_name].values.reshape(1, -1)
    distances, indices = model_knn.kneighbors(customer_vector, n_neighbors=top_n + 1)

    similar_customers = user_ts_matrix.index[indices.flatten()[1:]]
    similar_df = df[df['Заказчик'].isin(similar_customers)]

    recommendations = (
        similar_df['ТС']
            .value_counts()
            .head(top_n)
            .reset_index()
            .rename(columns={'index': 'ТС', 'ТС': 'Частота'})
    )
    return recommendations


# Пример
customer_example = df['Заказчик'].iloc[0]
recs = recommend_ts_for_customer(customer_example)
print(f"Рекомендации для клиента: {customer_example}")
print(recs)

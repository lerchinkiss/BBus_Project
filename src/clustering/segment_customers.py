from common_imports import *
from link_tables import apply_links
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
import os
from common_imports import OUTPUTS_DIR

# Загрузка и подготовка
df = pd.read_excel(os.path.join(DATA_DIR, "filtered_datasets", "bbOrders_filtered.xlsx"))
df = apply_links(df)

# Очистка и преобразование
df = df[df['Заказчик'].notna()]
df['ФактическаяСтоимость'] = pd.to_numeric(df['ФактическаяСтоимость'], errors='coerce')
df['КоличествоПассажиров'] = pd.to_numeric(df['КоличествоПассажиров'], errors='coerce')
df['ВремяНачала'] = pd.to_datetime(df['ВремяНачала'], errors='coerce')

# Вспомогательные признаки
df['Маршрут'] = df['Загрузка'].astype(str) + " → " + df['Разгрузка'].astype(str)
df['Час'] = df['ВремяНачала'].dt.hour
df['ВремяСуток'] = pd.cut(df['Час'], bins=[-1, 5, 11, 17, 23], labels=['Ночь', 'Утро', 'День', 'Вечер'])

# Функция для модального значения
def mode_or_nan(series):
    return series.mode().iloc[0] if not series.mode().empty else np.nan

# Группировка по заказчику
customer_df = df.groupby('Заказчик').agg({
    'ФактическаяСтоимость': ['count', 'mean', 'sum', 'std'],
    'КоличествоПассажиров': ['mean', 'sum', 'std'],
    'Маршрут': ['nunique', mode_or_nan],
    'ТипТС': [mode_or_nan, 'nunique'],
    'ВремяСуток': mode_or_nan,
    'Час': ['mean', 'std'],
    'Date': lambda x: (x.max() - x.min()).days if len(x) > 1 else 0
}).reset_index()

# Переименуем колонки
customer_df.columns = [
    'Заказчик', 'Кол_заказов', 'Сред_стоимость', 'Общ_стоимость', 'Стд_стоимость',
    'Сред_пассажиров', 'Общ_пассажиров', 'Стд_пассажиров',
    'Уник_маршрутов', 'Популярный_маршрут',
    'ЛюбимыйТипТС', 'Разнообразие_ТС',
    'ВремяСуток',
    'Средний_час', 'Стд_час',
    'Период_активности'
]

# Кодируем категориальные признаки
cat_features = ['ЛюбимыйТипТС', 'ВремяСуток']
customer_df[cat_features] = customer_df[cat_features].astype(str)
encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
encoded = encoder.fit_transform(customer_df[cat_features])
encoded_df = pd.DataFrame(encoded, columns=encoder.get_feature_names_out(cat_features))

# Объединяем с числовыми
features = pd.concat([
    customer_df[['Кол_заказов', 'Сред_стоимость', 'Общ_стоимость', 'Стд_стоимость',
                'Сред_пассажиров', 'Общ_пассажиров', 'Стд_пассажиров',
                'Уник_маршрутов', 'Разнообразие_ТС',
                'Средний_час', 'Стд_час',
                'Период_активности']],
    encoded_df
], axis=1).fillna(0)

# Масштабирование
scaler = StandardScaler()
X_scaled = scaler.fit_transform(features)

# Определение оптимального количества кластеров
inertias = []
K = range(1, 11)
for k in K:
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(X_scaled)
    inertias.append(kmeans.inertia_)

# Визуализация метода локтя
plt.figure(figsize=(10, 6))
plt.plot(K, inertias, 'bx-')
plt.xlabel('k')
plt.ylabel('Inertia')
plt.title('Elbow Method For Optimal k')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUTS_DIR, 'kmeans_elbow_method.png'))
plt.show()

# Кластеризация с оптимальным k
optimal_k = 4  # Определено на основе графика
kmeans = KMeans(n_clusters=optimal_k, random_state=42)
customer_df['Кластер'] = kmeans.fit_predict(X_scaled)

# PCA для визуализации
pca = PCA(n_components=2)
pca_result = pca.fit_transform(X_scaled)
customer_df['PCA1'] = pca_result[:, 0]
customer_df['PCA2'] = pca_result[:, 1]

# 1. Основная визуализация кластеров
plt.figure(figsize=(10, 6))
sns.scatterplot(data=customer_df, x='PCA1', y='PCA2', hue='Кластер', palette='tab10')
plt.title("Кластеризация заказчиков")
plt.xlabel("PCA 1")
plt.ylabel("PCA 2")
plt.legend(title="Кластер")
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUTS_DIR, 'customer_clusters.png'))
plt.close()

# 2. Распределение по количеству заказов
plt.figure(figsize=(10, 6))
sns.boxplot(data=customer_df, x='Кластер', y='Кол_заказов', palette='tab10')
plt.title(" Распределение количества заказов по кластерам")
plt.xlabel("Кластер")
plt.ylabel("Количество заказов")
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUTS_DIR, 'orders_distribution.png'))
plt.close()

# 3. Распределение по средней стоимости
plt.figure(figsize=(10, 6))
sns.boxplot(data=customer_df, x='Кластер', y='Сред_стоимость', palette='tab10')
plt.title("Распределение средней стоимости по кластерам")
plt.xlabel("Кластер")
plt.ylabel("Средняя стоимость")
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUTS_DIR, 'cost_distribution.png'))
plt.close()

# Сводка по кластерам
logger.info("\n Средние значения по кластерам:")
cluster_stats = customer_df.groupby('Кластер').agg({
    'Кол_заказов': ['mean', 'std'],
    'Сред_стоимость': ['mean', 'std'],
    'Сред_пассажиров': ['mean', 'std'],
    'Разнообразие_ТС': ['mean', 'std'],
    'Период_активности': ['mean', 'std']
}).round(2)
logger.info(cluster_stats)

# Описание кластеров
logger.info("\n Описание кластеров:")
for cluster in sorted(customer_df['Кластер'].unique()):
    cluster_data = customer_df[customer_df['Кластер'] == cluster]
    logger.info(f"\nКластер {cluster}:")
    logger.info(f"Количество заказчиков: {len(cluster_data)}")
    logger.info(f"Среднее количество заказов: {cluster_data['Кол_заказов'].mean():.2f}")
    logger.info(f"Средняя стоимость заказа: {cluster_data['Сред_стоимость'].mean():.2f}")
    logger.info(f"Среднее количество пассажиров: {cluster_data['Сред_пассажиров'].mean():.2f}")
    logger.info("\nТоп-5 заказчиков по общей стоимости:")
    logger.info(cluster_data.nlargest(5, 'Общ_стоимость')[['Заказчик', 'Кол_заказов', 'Сред_стоимость']])

# Визуализация средних значений по кластерам
plt.figure(figsize=(12, 6))
cluster_analysis = customer_df.groupby('Кластер').agg({
    'Кол_заказов': ['mean', 'std'],
    'Сред_стоимость': ['mean', 'std'],
    'Сред_пассажиров': ['mean', 'std'],
    'Разнообразие_ТС': ['mean', 'std'],
    'Период_активности': ['mean', 'std']
}).round(2)
cluster_analysis.plot(kind='bar')
plt.title('Average Values by Cluster')
plt.xlabel('Cluster')
plt.ylabel('Value')
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUTS_DIR, 'cluster_characteristics.png'))
plt.show()

# Распределение размеров кластеров
plt.figure(figsize=(10, 6))
sns.countplot(data=customer_df, x='Кластер')
plt.title('Cluster Size Distribution')
plt.xlabel('Cluster')
plt.ylabel('Count')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUTS_DIR, 'cluster_size_distribution.png'))
plt.show()

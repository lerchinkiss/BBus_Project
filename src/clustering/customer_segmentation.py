from common_imports import *

# Настройка отображения
pd.set_option('display.max_columns', None)
plt.style.use('seaborn')
sns.set_palette("husl")

def preprocess_data(df):
    """Предобработка данных"""
    # Копируем датафрейм
    df_processed = df.copy()
    
    # Преобразование дат
    date_columns = ['Date', 'ВремяНачала', 'ДатаОплаты']
    for col in date_columns:
        # Заменяем 'Not Information' на NaN
        df_processed[col] = df_processed[col].replace('Not Information', pd.NA)
        # Преобразуем в datetime
        df_processed[col] = pd.to_datetime(df_processed[col], errors='coerce')
    
    # Создание новых признаков из Date (так как это основная дата заказа)
    df_processed['Год'] = df_processed['Date'].dt.year
    df_processed['Месяц'] = df_processed['Date'].dt.month
    df_processed['ДеньНедели'] = df_processed['Date'].dt.dayofweek
    
    # Преобразование булевых колонок
    bool_columns = ['СобственноеТС', 'Оплачено', 'ТребуетсяТуалет', 'Багаж']
    for col in bool_columns:
        df_processed[col] = df_processed[col].map({'True': 1, 'False': 0})
        # Заполняем пропущенные значения нулями
        df_processed[col] = df_processed[col].fillna(0)
    
    # Извлечение региона из адреса
    def extract_region(address):
        if isinstance(address, str):
            match = re.search(r'([А-Я][а-я]+\.?\s*[А-Я][а-я]+)', address)
            return match.group(1) if match else 'Неизвестно'
        return 'Неизвестно'
    
    df_processed['РегионЗагрузки'] = df_processed['ЗагрузкаАдрес'].apply(extract_region)
    df_processed['РегионРазгрузки'] = df_processed['РазгрузкаАдрес'].apply(extract_region)
    
    return df_processed

def create_customer_features(df):
    """Создание признаков для каждого клиента"""
    # Преобразуем числовые колонки в числовой формат
    numeric_columns = ['РасчетнаяСтоимость', 'ФактическаяСтоимость', 'ПланируемоеВремяРаботы', 'КоличествоПассажиров']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    customer_features = df.groupby('Заказчик').agg({
        'Number': 'count',  # Количество заказов
        'РасчетнаяСтоимость': ['mean', 'sum'],  # Средняя и общая стоимость
        'ПланируемоеВремяРаботы': 'mean',  # Средняя длительность заказа
        'КоличествоПассажиров': 'mean',  # Среднее количество пассажиров
        'СобственноеТС': 'mean',  # Доля заказов с собственным ТС
        'ТребуетсяТуалет': 'mean',  # Доля заказов с туалетом
        'Багаж': 'mean',  # Доля заказов с багажом
        'Оплачено': 'mean',  # Доля оплаченных заказов
        'Год': 'nunique',  # Количество лет активности
        'Месяц': 'nunique',  # Количество месяцев активности
    }).reset_index()
    
    # Переименование колонок
    customer_features.columns = CLUSTERING_FEATURES
    
    # Заполнение пропущенных значений
    numeric_features = customer_features.select_dtypes(include=[np.number]).columns
    imputer = SimpleImputer(strategy='median')
    customer_features[numeric_features] = imputer.fit_transform(customer_features[numeric_features])
    
    return customer_features

def find_optimal_clusters(data, max_clusters=10):
    """Поиск оптимального количества кластеров"""
    wcss = []
    silhouette_scores = []
    
    for n_clusters in range(2, max_clusters + 1):
        kmeans = KMeans(n_clusters=n_clusters, **KMEANS_PARAMS)
        kmeans.fit(data)
        wcss.append(kmeans.inertia_)
        silhouette_scores.append(silhouette_score(data, kmeans.labels_))
    
    # Визуализация результатов
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    
    ax1.plot(range(2, max_clusters + 1), wcss, marker='o')
    ax1.set_title('Метод локтя')
    ax1.set_xlabel('Количество кластеров')
    ax1.set_ylabel('WCSS')
    
    ax2.plot(range(2, max_clusters + 1), silhouette_scores, marker='o')
    ax2.set_title('Метод силуэта')
    ax2.set_xlabel('Количество кластеров')
    ax2.set_ylabel('Silhouette Score')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, 'clustering_analysis.png'))
    plt.close()
    
    # Возвращаем оптимальное количество кластеров
    optimal_clusters = np.argmax(silhouette_scores) + 2
    return optimal_clusters

def visualize_clusters(data, labels, features):
    """Визуализация кластеров"""
    # Создаем пары признаков для визуализации
    feature_pairs = [
        ('КоличествоЗаказов', 'СредняяСтоимость'),
        ('СредняяДлительность', 'СреднееКоличествоПассажиров'),
        ('ДоляСобственногоТС', 'ДоляОплаченныхЗаказов')
    ]
    
    for pair in feature_pairs:
        plt.figure(figsize=(10, 6))
        sns.scatterplot(
            data=data,
            x=pair[0],
            y=pair[1],
            hue=labels,
            palette='viridis',
            alpha=0.6
        )
        plt.title(f'Кластеры по признакам {pair[0]} и {pair[1]}')
        plt.savefig(os.path.join(OUTPUTS_DIR, f'clusters_{pair[0]}_{pair[1]}.png'))
        plt.close()

def analyze_clusters(data, labels):
    """Анализ характеристик кластеров"""
    data['Кластер'] = labels
    
    # Анализ средних значений по кластерам
    cluster_analysis = data.groupby('Кластер').agg({
        'КоличествоЗаказов': 'mean',
        'СредняяСтоимость': 'mean',
        'СредняяДлительность': 'mean',
        'СреднееКоличествоПассажиров': 'mean',
        'ДоляСобственногоТС': 'mean',
        'ДоляОплаченныхЗаказов': 'mean',
        'КоличествоЛетАктивности': 'mean'
    }).round(2)
    
    # Сохранение результатов анализа
    cluster_analysis.to_excel(os.path.join(OUTPUTS_DIR, 'cluster_analysis.xlsx'))
    
    return cluster_analysis

def main():
    # Загрузка данных
    logger.info("Загрузка данных...")
    df = pd.read_excel(os.path.join(DATA_DIR, "filtered_datasets", "bbOrders_filtered.xlsx"))
    
    # Предобработка данных
    logger.info("Предобработка данных...")
    df_processed = preprocess_data(df)
    
    # Создание признаков для клиентов
    logger.info("Создание признаков для клиентов...")
    customer_features = create_customer_features(df_processed)
    
    # Масштабирование признаков
    logger.info("Масштабирование признаков...")
    features_to_scale = customer_features.columns[1:]  # Все колонки кроме 'Заказчик'
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(customer_features[features_to_scale])
    
    # Поиск оптимального количества кластеров
    logger.info("Поиск оптимального количества кластеров...")
    optimal_clusters = find_optimal_clusters(scaled_features)
    logger.info(f"Оптимальное количество кластеров: {optimal_clusters}")
    
    # Кластеризация
    logger.info("Выполнение кластеризации...")
    kmeans = KMeans(n_clusters=optimal_clusters, **KMEANS_PARAMS)
    cluster_labels = kmeans.fit_predict(scaled_features)
    
    # Визуализация кластеров
    logger.info("Визуализация кластеров...")
    visualize_clusters(customer_features, cluster_labels, features_to_scale)
    
    # Анализ кластеров
    logger.info("Анализ кластеров...")
    cluster_analysis = analyze_clusters(customer_features, cluster_labels)
    logger.info("\nАнализ кластеров:")
    logger.info(cluster_analysis)
    
    logger.info("Анализ завершен. Результаты сохранены в файлы.")

if __name__ == "__main__":
    main() 
from link_tables import apply_links
from common_imports import *

def load_and_prepare_data():
    """Загрузка и подготовка данных"""
    df = pd.read_excel(os.path.join(DATA_DIR, "filtered_datasets", "bbOrders_filtered.xlsx"))
    df = apply_links(df)
    
    columns = [
        'ТипТС', 'КоличествоПассажиров', 'Заказчик', 'КонтактноеЛицо',
        'Организация', 'Ответсвенный', 'ТС', 'Водитель',
        'ЗагрузкаПункт', 'РазгрузкаПункт',
        'ТипЗаказа', 'Тариф', 'ФактическаяСтоимость', 'ЦенаЗаЧас',
        'Многодневный', 'ЗарубежнаяПоездка', 'ТребуетсяТуалет', 'Багаж'
    ]
    
    df = df[columns].dropna(subset=['ТипТС', 'КоличествоПассажиров'])
    df['Маршрут'] = df['ЗагрузкаПункт'].astype(str) + " → " + df['РазгрузкаПункт'].astype(str)
    df = df.drop(['ЗагрузкаПункт', 'РазгрузкаПункт'], axis=1)
    
    return df

def train_random_forest(df):
    """Обучение модели RandomForest"""
    target = 'ТипТС'
    features = [col for col in df.columns if col != target]
    
    # Кодирование категориальных признаков
    df_encoded = df.copy()
    encoders = {}
    for col in df_encoded.columns:
        if df_encoded[col].dtype == 'object':
            le = LabelEncoder()
            df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))
            encoders[col] = le
    
    X = df_encoded[features]
    y = df_encoded[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    
    # Обучение модели
    rf = RandomForestClassifier(**RF_PARAMS)
    rf.fit(X_train, y_train)
    
    # Анализ важности признаков
    importances = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)
    top_10 = importances.head(10).index.tolist()
    
    # Обучение на топ-10 признаках
    X_train_top = X_train[top_10]
    X_test_top = X_test[top_10]
    rf.fit(X_train_top, y_train)
    y_pred_rf = rf.predict(X_test_top)
    
    # Оценка качества
    logger.info("\nRandomForest Results:")
    logger.info(f"Accuracy: {accuracy_score(y_test, y_pred_rf)}")
    logger.info("\nClassification Report:")
    logger.info(classification_report(y_test, y_pred_rf))
    
    # Визуализация важности признаков
    plt.figure(figsize=(10, 6))
    sns.barplot(x=importances.head(10).values, y=importances.head(10).index)
    plt.title("Топ-10 признаков (RandomForest)")
    plt.xlabel("Важность")
    plt.tight_layout()
    plt.grid(True)
    plt.savefig(os.path.join(OUTPUTS_DIR, "feature_importance_rf.png"))
    plt.close()
    
    # Сохранение модели и энкодеров
    joblib.dump(rf, os.path.join(MODELS_DIR, "model_typeTS_rf.pkl"))
    joblib.dump(encoders, os.path.join(MODELS_DIR, "encoders.pkl"))
    
    return rf, encoders

def train_catboost(df):
    """Обучение модели CatBoost"""
    target = 'ТипТС'
    features = [col for col in df.columns if col != target]
    
    X = df[features]
    y = df[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    
    # Определение категориальных признаков
    cat_features = X.select_dtypes(include=['object']).columns.tolist()
    
    # Создание пулов данных
    train_pool = Pool(X_train, y_train, cat_features=cat_features)
    test_pool = Pool(X_test, y_test, cat_features=cat_features)
    
    # Обучение модели
    model = CatBoostClassifier(**CATBOOST_PARAMS)
    model.fit(train_pool)
    
    # Оценка качества
    y_pred = model.predict(test_pool)
    logger.info("\nCatBoost Results:")
    logger.info(f"Accuracy: {accuracy_score(y_test, y_pred)}")
    logger.info("\nClassification Report:")
    logger.info(classification_report(y_test, y_pred))
    
    # Анализ важности признаков
    feature_importance = model.get_feature_importance(prettified=True)
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Importances', y='Feature Id', data=feature_importance.head(10))
    plt.title("Топ-10 признаков (CatBoost)")
    plt.tight_layout()
    plt.grid(True)
    plt.savefig(os.path.join(OUTPUTS_DIR, "feature_importance_catboost.png"))
    plt.close()
    
    # Сохранение модели
    model.save_model(os.path.join(MODELS_DIR, "catboost_typeTS_model.cbm"))
    
    return model

def analyze_relationships(df):
    """Анализ взаимосвязей в данных"""
    logger.info("\n--- 📎 Анализ взаимосвязей ---")
    
    # Связь между Заказчиком и Организацией
    cross1 = pd.crosstab(df['Заказчик'], df['Организация'])
    logger.info("\nЗаказчик × Организация:")
    logger.info(f"- Уникальных связок: {len(cross1.stack())}")
    logger.info(f"- Среднее число организаций на заказчика: {cross1.astype(bool).sum(axis=1).mean()}")
    
    # Связь между Заказчиком и Контактным лицом
    cross2 = pd.crosstab(df['Заказчик'], df['КонтактноеЛицо'])
    logger.info("\nЗаказчик × КонтактноеЛицо:")
    logger.info(f"- Уникальных связок: {len(cross2.stack())}")
    logger.info(f"- Среднее число контактных лиц на заказчика: {cross2.astype(bool).sum(axis=1).mean()}")
    
    # Водитель ↔ ТС
    vod_tts = df.groupby('Водитель')['ТС'].nunique().sort_values(ascending=False)
    logger.info("\nВодитель × ТС:")
    logger.info(vod_tts.describe())
    
    plt.figure(figsize=(8, 4))
    sns.histplot(vod_tts, bins=20)
    plt.title("Распределение количества ТС на одного водителя")
    plt.xlabel("Уникальных ТС")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, "driver_ts_distribution.png"))
    plt.close()
    
    # ТипТС ↔ ТС
    tts_typets = df.groupby('ТС')['ТипТС'].nunique().sort_values(ascending=False)
    logger.info("\nТС × ТипТС:")
    logger.info(tts_typets.describe())
    
    plt.figure(figsize=(8, 4))
    sns.histplot(tts_typets, bins=10)
    plt.title("Распределение количества ТипТС на одну ТС")
    plt.xlabel("Уникальных ТипТС")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, "ts_typets_distribution.png"))
    plt.close()

def main():
    """Основная функция"""
    logger.info("=== Начало обучения моделей ===")
    
    # Загрузка данных
    df = load_and_prepare_data()
    
    # Обучение моделей
    rf_model, encoders = train_random_forest(df)
    catboost_model = train_catboost(df)
    
    # Анализ взаимосвязей
    analyze_relationships(df)
    
    logger.info("\n=== Обучение завершено ===")
    logger.info("Модели сохранены в outputs/models/")
    logger.info("Графики сохранены в outputs/")

if __name__ == "__main__":
    main()


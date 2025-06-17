from common_imports import *

# === Обучение новой CatBoost модели ===

# Загрузка подготовленных данных
logger.info("\nЗагрузка признаков и целевой переменной...")
X = pd.read_excel(os.path.join(PREPARED_DATA_DIR, "X_train_ready.xlsx"))
y = pd.read_excel(os.path.join(PREPARED_DATA_DIR, "y_train_ready.xlsx"))

# Разделение на обучающую и тестовую выборки
logger.info("Разделение на train/test...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE)

# Определяем категориальные признаки
cat_features = ['Заказчик', 'ТипЗаказа', 'ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа']

# Обучающий пул
train_pool = Pool(X_train, y_train, cat_features=cat_features)
test_pool = Pool(X_test, y_test, cat_features=cat_features)

# Создание модели
logger.info("\nОбучение модели CatBoost...")
model = CatBoostClassifier(
    iterations=500,
    depth=6,
    learning_rate=0.1,
    loss_function='MultiClass',
    random_seed=RANDOM_STATE,
    verbose=100,
    early_stopping_rounds=50
)

model.fit(train_pool)

# Оценка качества
logger.info("\nОценка качества модели...")
y_pred = model.predict(test_pool)

logger.info(f"Accuracy: {accuracy_score(y_test, y_pred)}")
logger.info("\nClassification Report:")
logger.info(classification_report(y_test, y_pred))

# Сохранение модели
logger.info("\nСохранение модели в папку models/...")
model.save_model(os.path.join(MODELS_DIR, "catboost_typets_model_v3.cbm"))

logger.info("\nМодель успешно сохранена в models/catboost_typets_model_v3.cbm")

from common_imports import *

# Определяем абсолютные пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PREPARED_DATA_DIR = os.path.join(DATA_DIR, "prepared_data")
MODELS_DIR = os.path.join(BASE_DIR, "outputs", "models")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

# Загрузка подготовленных данных
logger.info("Загрузка подготовленных данных...")
X = pd.read_excel(os.path.join(PREPARED_DATA_DIR, "X_train_ready_rf.xlsx"))
y = pd.read_excel(os.path.join(PREPARED_DATA_DIR, "y_train_ready_rf.xlsx"))

# Разделение на обучающую и тестовую выборки
logger.info("Разделение данных на обучающую и тестовую выборки...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
)

# Создание и обучение модели
logger.info("Обучение модели RandomForest...")
rf_model = RandomForestClassifier(**RF_PARAMS)
rf_model.fit(X_train, y_train.values.ravel())

# Оценка качества модели
logger.info("Оценка качества модели...")
y_pred = rf_model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
logger.info(f"Точность модели на тестовой выборке: {accuracy:.4f}")

# Подробный отчет о качестве классификации
logger.info("Отчет о классификации:")
logger.info(classification_report(y_test, y_pred))

# Анализ важности признаков
logger.info("Анализ важности признаков...")
feature_importance = pd.DataFrame({
    'Признак': X.columns,
    'Важность': rf_model.feature_importances_
})
feature_importance = feature_importance.sort_values('Важность', ascending=False)

# Визуализация важности признаков
plt.figure(figsize=(10, 6))
sns.barplot(x='Важность', y='Признак', data=feature_importance)
plt.title('Важность признаков (RandomForest)')
plt.tight_layout()

# Сохранение графика
plt.savefig(os.path.join(OUTPUTS_DIR, 'feature_importance_randomforest.png'))
logger.info(f"График важности признаков сохранен в: {os.path.join(OUTPUTS_DIR, 'feature_importance_randomforest.png')}")

# Сохранение модели
logger.info("Сохранение модели...")
joblib.dump(rf_model, os.path.join(MODELS_DIR, "randomforest_typets_model.pkl"))

logger.info("Обучение модели RandomForest завершено!")
logger.info(f"Модель сохранена в: {os.path.join(MODELS_DIR, 'randomforest_typets_model.pkl')}")
logger.info(f"Точность на тестовой выборке: {accuracy:.4f}")

# Визуализация результатов
plt.figure(figsize=(12, 8))
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix - Random Forest Classification')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUTS_DIR, 'rf_confusion_matrix.png'))
plt.show()

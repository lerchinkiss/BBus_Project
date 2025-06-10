from common_imports import *

# Определяем абсолютные пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PREPARED_DATA_DIR = os.path.join(DATA_DIR, "prepared_data")
MODELS_DIR = os.path.join(BASE_DIR, "outputs", "models")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

def load_data():
    """Загрузка данных для обеих моделей"""
    logger.info("Загрузка данных...")
    
    # Данные для CatBoost
    X_cat = pd.read_excel(os.path.join(PREPARED_DATA_DIR, "X_train_ready.xlsx"))
    y_cat = pd.read_excel(os.path.join(PREPARED_DATA_DIR, "y_train_ready.xlsx"))
    
    # Данные для RandomForest
    X_rf = pd.read_excel(os.path.join(PREPARED_DATA_DIR, "X_train_ready_rf.xlsx"))
    y_rf = pd.read_excel(os.path.join(PREPARED_DATA_DIR, "y_train_ready_rf.xlsx"))
    
    return X_cat, y_cat, X_rf, y_rf

def load_models():
    """Загрузка обученных моделей"""
    logger.info("Загрузка моделей...")
    
    # Загрузка CatBoost
    catboost_model = CatBoostClassifier()
    catboost_model.load_model(os.path.join(MODELS_DIR, "catboost_typets_model_v3.cbm"))
    
    # Загрузка RandomForest
    rf_model = joblib.load(os.path.join(MODELS_DIR, "randomforest_typets_model.pkl"))
    
    return catboost_model, rf_model

def evaluate_model(model, X, y, model_name):
    """Оценка качества модели"""
    logger.info(f"Оценка модели {model_name}...")
    
    # Предсказания
    y_pred = model.predict(X)
    accuracy = accuracy_score(y, y_pred)
    
    logger.info(f"Точность модели {model_name}: {accuracy:.4f}")
    logger.info("Отчет о классификации:")
    logger.info(classification_report(y, y_pred))
    
    return accuracy, y_pred

def plot_confusion_matrix(y_true, y_pred, model_name):
    """Построение матрицы ошибок"""
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(15, 10))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title(f'Матрица ошибок - {model_name}')
    plt.ylabel('Истинный класс')
    plt.xlabel('Предсказанный класс')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, f'confusion_matrix_{model_name.lower()}.png'))
    plt.close()

def plot_model_comparison(models_results):
    """Построение графика сравнения моделей"""
    plt.figure(figsize=(12, 6))
    metrics = ['accuracy', 'precision', 'recall', 'f1']
    x = np.arange(len(metrics))
    width = 0.2
    
    for i, (model_name, results) in enumerate(models_results.items()):
        plt.bar(x + i*width, [results[m] for m in metrics], width, label=model_name)
    
    plt.xlabel('Метрики')
    plt.ylabel('Значение')
    plt.title('Сравнение моделей по метрикам')
    plt.xticks(x + width, metrics)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, 'model_comparison.png'))
    plt.close()

def compare_predictions(y_true, y_pred_cat, y_pred_rf):
    """Сравнение предсказаний моделей"""
    # Преобразуем все данные в одномерные массивы
    y_true = y_true.values.ravel() if hasattr(y_true, 'values') else y_true
    y_pred_cat = y_pred_cat.ravel() if hasattr(y_pred_cat, 'ravel') else y_pred_cat
    y_pred_rf = y_pred_rf.ravel() if hasattr(y_pred_rf, 'ravel') else y_pred_rf
    
    comparison = pd.DataFrame({
        'Истинное значение': y_true,
        'CatBoost': y_pred_cat,
        'RandomForest': y_pred_rf
    })
    
    # Добавляем столбец с информацией о совпадении предсказаний
    comparison['Модели согласны'] = comparison['CatBoost'] == comparison['RandomForest']
    comparison['Правильно предсказано'] = (comparison['CatBoost'] == comparison['Истинное значение']) & \
                                        (comparison['RandomForest'] == comparison['Истинное значение'])
    
    # Анализ результатов
    total = len(comparison)
    models_agree = comparison['Модели согласны'].sum()
    both_correct = comparison['Правильно предсказано'].sum()
    
    logger.info("Сравнение предсказаний моделей:")
    logger.info(f"Всего примеров: {total}")
    logger.info(f"Модели согласны друг с другом: {models_agree} ({models_agree/total*100:.2f}%)")
    logger.info(f"Обе модели правильно предсказали: {both_correct} ({both_correct/total*100:.2f}%)")
    
    # Анализ расхождений
    disagreements = comparison[~comparison['Модели согласны']]
    logger.info("Анализ расхождений в предсказаниях:")
    logger.info(f"Количество расхождений: {len(disagreements)} ({len(disagreements)/total*100:.2f}%)")
    
    # Сохраняем результаты сравнения
    comparison.to_excel(os.path.join(OUTPUTS_DIR, 'model_predictions_comparison.xlsx'), index=False)
    logger.info(f"Подробное сравнение сохранено в: {os.path.join(OUTPUTS_DIR, 'model_predictions_comparison.xlsx')}")

def main():
    """Основная функция сравнения моделей"""
    # Загрузка данных и моделей
    X_cat, y_cat, X_rf, y_rf = load_data()
    catboost_model, rf_model = load_models()
    
    # Оценка моделей
    cat_accuracy, y_pred_cat = evaluate_model(catboost_model, X_cat, y_cat, "CatBoost")
    rf_accuracy, y_pred_rf = evaluate_model(rf_model, X_rf, y_rf, "RandomForest")
    
    # Построение матриц ошибок
    plot_confusion_matrix(y_cat, y_pred_cat, "CatBoost")
    plot_confusion_matrix(y_rf, y_pred_rf, "RandomForest")
    
    # Сравнение предсказаний
    compare_predictions(y_cat, y_pred_cat, y_pred_rf)
    
    # Визуализация сравнения точности
    plt.figure(figsize=(8, 6))
    models = ['CatBoost', 'RandomForest']
    accuracies = [cat_accuracy, rf_accuracy]
    
    sns.barplot(x=models, y=accuracies)
    plt.title('Сравнение точности моделей')
    plt.ylabel('Точность')
    plt.ylim(0.9, 1.0)  # Устанавливаем диапазон для лучшей визуализации различий
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, 'models_accuracy_comparison.png'))
    logger.info(f"График сравнения точности моделей сохранен в: {os.path.join(OUTPUTS_DIR, 'models_accuracy_comparison.png')}")

if __name__ == "__main__":
    main() 
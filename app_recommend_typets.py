import pandas as pd
import os
from catboost import CatBoostClassifier, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# === Шаг 3: Обучение новой CatBoost модели ===

# Загрузка подготовленных данных
print("\nЗагрузка признаков и целевой переменной...")
X = pd.read_excel(os.path.join("prepared_data", "X_train_ready.xlsx"))
y = pd.read_excel(os.path.join("prepared_data", "y_train_ready.xlsx"))

# Разделение на обучающую и тестовую выборки
print("Разделение на train/test...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Определяем категориальные признаки
cat_features = ['Заказчик', 'ТипЗаказа', 'ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа']

# Обучающий пул
train_pool = Pool(X_train, y_train, cat_features=cat_features)
test_pool = Pool(X_test, y_test, cat_features=cat_features)

# Создание модели
print("\nОбучение модели CatBoost...")
model = CatBoostClassifier(
    iterations=500,
    depth=6,
    learning_rate=0.1,
    loss_function='MultiClass',
    random_seed=42,
    verbose=100,
    early_stopping_rounds=50
)

model.fit(train_pool)

# Оценка качества
print("\nОценка качества модели...")
y_pred = model.predict(test_pool)

print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# Сохранение модели
print("\nСохранение модели в папку models/...")
os.makedirs("models", exist_ok=True)
model.save_model(os.path.join("models", "catboost_typets_model_v3.cbm"))

print("\nМодель успешно сохранена в models/catboost_typets_model_v3.cbm")

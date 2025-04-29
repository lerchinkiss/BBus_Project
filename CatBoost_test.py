import pandas as pd
import os
import joblib
from catboost import CatBoostClassifier, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

# === 1. Загрузка данных ===
print("\nЗагрузка данных...")
DATA_PATH = "filtered_datasets/bbOrders_filtered.xlsx"
df = pd.read_excel(DATA_PATH)

# === 2. Предобработка под новую задачу ===
print("\nПредобработка...")

# Оставляем только нужные столбцы
df = df[['Заказчик', 'КоличествоПассажиров', 'ЦенаЗаЧас', 'ТипЗаказа', 'ТипТС']]

# Убираем пропуски по целевому и ключевым признакам
df = df.dropna(subset=['ТипТС', 'КоличествоПассажиров', 'ЦенаЗаЧас', 'ТипЗаказа'])

# Заполняем пропуски в названии заказчиков
df['Заказчик'] = df['Заказчик'].fillna('Новый заказчик')

# Целевая переменная
target = 'ТипТС'
features = ['Заказчик', 'КоличествоПассажиров', 'ЦенаЗаЧас', 'ТипЗаказа']

# Разделение на train/test
X = df[features]
y = df[target]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Определяем категориальные признаки
cat_features = ['Заказчик', 'ТипЗаказа']

# Обучающий пул данных
train_pool = Pool(X_train, y_train, cat_features=cat_features)
test_pool = Pool(X_test, y_test, cat_features=cat_features)

# === 3. Обучение модели ===
print("\nОбучение CatBoostClassifier...")
model = CatBoostClassifier(
    iterations=500,
    depth=6,
    learning_rate=0.1,
    loss_function='MultiClass',
    random_seed=42,
    verbose=100
)
model.fit(train_pool)

# === 4. Оценка качества ===
print("\nОценка качества модели...")
y_pred = model.predict(test_pool)

print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# === 5. Важность признаков ===
print("\nАнализ важности признаков...")
feature_importance = model.get_feature_importance(prettified=True)

plt.figure(figsize=(8, 5))
sns.barplot(x='Importances', y='Feature Id', data=feature_importance)
plt.title("Важность признаков для рекомендации типа ТС")
plt.tight_layout()
plt.grid(True)
plt.savefig("feature_importance_catboost.png")
plt.show()

# === 6. Сохранение модели ===
model.save_model("catboost_typets_model_v2.cbm")
print("CМодель успешно сохранена: catboost_typets_model_v2.cbm")

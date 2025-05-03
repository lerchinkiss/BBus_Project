import os
import pandas as pd
from catboost import CatBoostClassifier, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from link_tables import apply_links

# === Загрузка данных ===
df = pd.read_excel(os.path.join("filtered_datasets", "bbOrders_filtered.xlsx"))
df = apply_links(df)

# Выбор признаков
columns = [
    'ТипТС', 'КоличествоПассажиров', 'ЦенаЗаЧас', 'ФактическаяСтоимость',
    'ТС', 'Водитель', 'Тариф', 'ТипЗаказа', 'Заказчик',
    'ЗагрузкаПункт', 'РазгрузкаПункт'
]

df = df[columns].dropna(subset=['ТипТС', 'КоличествоПассажиров'])

# Объединяем маршрут
df['Маршрут'] = df['ЗагрузкаПункт'].astype(str) + ' → ' + df['РазгрузкаПункт'].astype(str)
df = df.drop(['ЗагрузкаПункт', 'РазгрузкаПункт'], axis=1)

# Целевая переменная
target = 'ТипТС'
features = [col for col in df.columns if col != target]

# Разделение
X = df[features]
y = df[target]

# Разделение train/test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Определим категориальные признаки
cat_features = X.select_dtypes(include=['object']).columns.tolist()

# Обучающий пул
train_pool = Pool(X_train, y_train, cat_features=cat_features)
test_pool = Pool(X_test, y_test, cat_features=cat_features)

# Обучение модели
model = CatBoostClassifier(verbose=100, random_state=42)
model.fit(train_pool)

# Предсказание
y_pred = model.predict(test_pool)

# Оценка
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# Сохраняем модель
model.save_model("catboost_typeTS_model.cbm")
print("Модель сохранена в catboost_typeTS_model.cbm")

# Важность признаков
feature_importance = model.get_feature_importance(prettified=True)
plt.figure(figsize=(10, 6))
sns.barplot(x='Importances', y='Feature Id', data=feature_importance.head(10))
plt.title("Топ-10 признаков (CatBoost)")
plt.tight_layout()
plt.grid(True)
plt.show()

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

from link_tables import apply_links

df = pd.read_excel(os.path.join("filtered_datasets", "bbOrders_filtered.xlsx"))
df = apply_links(df)

columns = [
    'ТипТС', 'КоличествоПассажиров', 'Заказчик', 'КонтактноеЛицо',
    'Организация', 'Ответсвенный', 'ТС', 'Водитель',
    'ЗагрузкаПункт', 'РазгрузкаПункт',
    'ТипЗаказа', 'Тариф', 'ФактическаяСтоимость', 'ЦенаЗаЧас',
    'Многодневный', 'ЗарубежнаяПоездка', 'ТребуетсяТуалет', 'Багаж'
]

df = df[columns].dropna(subset=['ТипТС', 'КоличествоПассажиров'])

# Добавим объединённый признак "Маршрут"
df['Маршрут'] = df['ЗагрузкаПункт'].astype(str) + " → " + df['РазгрузкаПункт'].astype(str)
df = df.drop(['ЗагрузкаПункт', 'РазгрузкаПункт'], axis=1)

target = 'ТипТС'
features = [col for col in df.columns if col != target]

df_encoded = df.copy()
encoders = {}

for col in df_encoded.columns:
    if df_encoded[col].dtype == 'object':
        le = LabelEncoder()
        df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))
        encoders[col] = le

X = df_encoded[features]
y = df_encoded[target]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)

importances = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)
top_10 = importances.head(10).index.tolist()

X_train_top = X_train[top_10]
X_test_top = X_test[top_10]

rf.fit(X_train_top, y_train)
y_pred_rf = rf.predict(X_test_top)

print("Accuracy:", accuracy_score(y_test, y_pred_rf))
print("\nClassification Report:\n", classification_report(y_test, y_pred_rf))

joblib.dump(rf, 'models/model_typeTS.pkl')
joblib.dump(encoders, 'models/encoders.pkl')

plt.figure(figsize=(10, 6))
sns.barplot(x=importances.head(10).values, y=importances.head(10).index)
plt.title("Топ-10 признаков для предсказания ТипТС (RandomForest)")
plt.xlabel("Важность")
plt.tight_layout()
plt.grid(True)
plt.show()


# Анализ взаимосвязей
import seaborn as sns
import matplotlib.pyplot as plt

print("\n--- 📎 Проверка связей ---")

# Связь между Заказчиком и Организацией
cross1 = pd.crosstab(df['Заказчик'], df['Организация'])
print("\nЗаказчик × Организация — уникальных связок:", len(cross1.stack()))
print("Число организаций на одного заказчика (среднее):", cross1.astype(bool).sum(axis=1).mean())

# Связь между Заказчиком и Контактным лицом
cross2 = pd.crosstab(df['Заказчик'], df['КонтактноеЛицо'])
print("\nЗаказчик × КонтактноеЛицо — уникальных связок:", len(cross2.stack()))
print("Число контактных лиц на одного заказчика (среднее):", cross2.astype(bool).sum(axis=1).mean())

# Связь между Заказчиком и Ответственным
cross3 = pd.crosstab(df['Заказчик'], df['Ответсвенный'])
print("\nЗаказчик × Ответсвенный — уникальных связок:", len(cross3.stack()))
print("Ответственных на одного заказчика (среднее):", cross3.astype(bool).sum(axis=1).mean())

# Водитель ↔ ТС
print("\nВодитель × ТС (на сколько ТС работает 1 водитель):")
vod_tts = df.groupby('Водитель')['ТС'].nunique().sort_values(ascending=False)
print(vod_tts.describe())
plt.figure(figsize=(8, 4))
sns.histplot(vod_tts, bins=20)
plt.title("Распределение количества ТС на одного водителя")
plt.xlabel("Уникальных ТС")
plt.tight_layout()
plt.show()

# ТипТС ↔ ТС (связь типа транспорта и конкретной ТС)
print("\nТС × ТипТС — сколько ТС работают под разными типами транспорта:")
tts_typets = df.groupby('ТС')['ТипТС'].nunique().sort_values(ascending=False)
print(tts_typets.describe())
plt.figure(figsize=(8, 4))
sns.histplot(tts_typets, bins=10)
plt.title("Распределение количества ТипТС на одну ТС")
plt.xlabel("Уникальных ТипТС")
plt.tight_layout()
plt.show()


from common_imports import *

# Добавить корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from link_tables import apply_links

# Определяем абсолютные пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PREPARED_DATA_DIR = os.path.join(DATA_DIR, "prepared_data")
MODELS_DIR = os.path.join(BASE_DIR, "outputs", "models")

# === Подготовка обучающего набора ===
logger.info("Загрузка данных заказов...")
orders_df = pd.read_excel(os.path.join(DATA_DIR, "filtered_datasets", "bbOrders_filtered.xlsx"))
orders_df = apply_links(orders_df)

# Загрузка подготовленного профиля заказчиков
logger.info("Загрузка профиля заказчиков...")
customer_profile = pd.read_excel(os.path.join(PREPARED_DATA_DIR, "customer_profile.xlsx"))

# Объединение заказов с профилем заказчиков
logger.info("Объединение заказов с профилем...")
full_df = orders_df.merge(customer_profile, on='Заказчик', how='left')

# Если заказчик новый (нет профиля) — заполняем "Неизвестно"
for col in ['ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа']:
    full_df[col] = full_df[col].fillna('Неизвестно')

# Оставляем только нужные признаки для обучения
FEATURES = [
    'Заказчик',
    'КоличествоПассажиров',
    'ЦенаЗаЧас',
    'ТипЗаказа',
    'ЛюбимыйТипТС',
    'ИсторическийЛюбимыйТС',
    'ЛюбимыйСтатусЗаказа'
]
TARGET = 'ТипТС'

# Удаляем строки с пропущенными значениями
full_df = full_df.dropna(subset=[TARGET, 'КоличествоПассажиров', 'ЦенаЗаЧас', 'ТипЗаказа'])

# Кодирование категориальных признаков
logger.info("Кодирование категориальных признаков...")
encoders = {}
X_encoded = full_df[FEATURES].copy()

# Кодируем каждый категориальный признак
for col in FEATURES:
    encoder = LabelEncoder()
    X_encoded[col] = encoder.fit_transform(X_encoded[col].astype(str))
    encoders[col] = encoder

# Сохраняем энкодеры
logger.info("Сохранение энкодеров...")
joblib.dump(encoders, os.path.join(MODELS_DIR, "randomforest_encoders.pkl"))

# Сохраняем подготовленные данные
logger.info("Сохранение подготовленного набора данных...")
X_encoded.to_excel(os.path.join(PREPARED_DATA_DIR, "X_train_ready_rf.xlsx"), index=False)
full_df[TARGET].to_excel(os.path.join(PREPARED_DATA_DIR, "y_train_ready_rf.xlsx"), index=False)

logger.info("Данные для обучения RandomForest сохранены:")
logger.info(f"- Признаки: {os.path.join(PREPARED_DATA_DIR, 'X_train_ready_rf.xlsx')}")
logger.info(f"- Целевая переменная: {os.path.join(PREPARED_DATA_DIR, 'y_train_ready_rf.xlsx')}")
logger.info(f"- Энкодеры: {os.path.join(MODELS_DIR, 'randomforest_encoders.pkl')}") 
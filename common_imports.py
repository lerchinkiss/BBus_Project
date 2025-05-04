import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import logging
from datetime import datetime
import re

# Импорты для машинного обучения
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, silhouette_score
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from catboost import CatBoostClassifier, Pool

# Добавляем корневую директорию в путь
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Импорты из проекта
from link_tables import apply_links

# Определяем основные пути
DATA_DIR = os.path.join(BASE_DIR, "data")
PREPARED_DATA_DIR = os.path.join(DATA_DIR, "prepared_data")
MODELS_DIR = os.path.join(BASE_DIR, "outputs", "models")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Создаем директории, если их нет
for dir_path in [DATA_DIR, PREPARED_DATA_DIR, MODELS_DIR, OUTPUTS_DIR, LOGS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, f'app_{datetime.now().strftime("%Y%m%d")}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Настройка отображения pandas и matplotlib
pd.set_option('display.max_columns', None)
plt.style.use('seaborn')
sns.set_palette("husl")

# Константы для моделей
RANDOM_STATE = 42
TEST_SIZE = 0.2

# Параметры моделей
RF_PARAMS = {
    'n_estimators': 100,
    'max_depth': 10,
    'min_samples_split': 5,
    'min_samples_leaf': 2,
    'random_state': RANDOM_STATE,
    'n_jobs': -1
}

CATBOOST_PARAMS = {
    'iterations': 500,
    'depth': 6,
    'learning_rate': 0.1,
    'loss_function': 'MultiClass',
    'random_seed': RANDOM_STATE,
    'verbose': 100,
    'early_stopping_rounds': 50
}

# Параметры кластеризации
KMEANS_PARAMS = {
    'random_state': RANDOM_STATE,
    'n_init': 10
}

# Список признаков для моделей
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

# Категориальные признаки
CATEGORICAL_FEATURES = ['Заказчик', 'ТипЗаказа', 'ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа']

# Признаки для кластеризации
CLUSTERING_FEATURES = [
    'КоличествоЗаказов',
    'СредняяСтоимость',
    'ОбщаяСтоимость',
    'СредняяДлительность',
    'СреднееКоличествоПассажиров',
    'ДоляСобственногоТС',
    'ДоляЗаказовСТуалетом',
    'ДоляЗаказовСБагажом',
    'ДоляОплаченныхЗаказов',
    'КоличествоЛетАктивности',
    'КоличествоМесяцевАктивности'
] 
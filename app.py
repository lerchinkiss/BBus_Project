from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import os
import json
from datetime import datetime
from catboost import CatBoostClassifier, Pool
from link_tables import apply_links
from src.web.save_order_data import save_order_data, sheet
import pickle
import time

app = Flask(__name__, static_folder='docs')
CORS(app)

# Абсолютные пути
BASE_DIR = os.path.dirname(__file__)
CACHE_FILE = os.path.join(BASE_DIR, 'outputs/data_cache.pkl')
FLEET_FILE = os.path.join(BASE_DIR, 'docs/fleet.json')
CACHE_TIMEOUT = 3600

# Загрузка автопарка
with open(FLEET_FILE, 'r', encoding='utf-8') as f:
    fleet_info = json.load(f)

# Кэш

def save_to_cache(data):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump({'timestamp': time.time(), 'data': data}, f)

def load_from_cache():
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'rb') as f:
                cache = pickle.load(f)
                if time.time() - cache['timestamp'] < CACHE_TIMEOUT:
                    return cache['data']
    except:
        pass
    return None

# Загрузка модели
print("Загрузка модели...")
model = CatBoostClassifier()
model_path = os.path.abspath("outputs/models/catboost_typets_model_v3.cbm")
print("Загружаем модель", model_path)
model.load_model(model_path)

# Загрузка данных
orders_df, customer_profile, type_ts_mapping = (None, None, None)

def load_data():
    global orders_df, customer_profile, type_ts_mapping
    cached_data = load_from_cache()
    if cached_data:
        print("Данные из кэша")
        orders_df, customer_profile, type_ts_mapping = cached_data
        return

    orders_df = pd.read_excel("data/filtered_datasets/bbOrders_filtered.xlsx")
    orders_df = apply_links(orders_df)
    customer_profile = pd.read_excel("data/prepared_data/customer_profile.xlsx")
    type_ts_df = pd.read_excel("data/filtered_datasets/uatTypeTS_filtered.xlsx")
    type_ts_df = type_ts_df.dropna(subset=['Description', 'МаксМест'])
    type_ts_mapping = dict(zip(type_ts_df['Description'], type_ts_df['МаксМест']))
    save_to_cache((orders_df, customer_profile, type_ts_mapping))

load_data()

@app.route('/')
def index():
    return send_from_directory('docs', 'index.html')

@app.route('/api/companies')
def get_companies():
    try:
        companies = orders_df['Заказчик'].dropna().unique().tolist()
        companies.sort()
        return jsonify(companies)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/customer_profile/<company>')
def get_customer_profile(company):
    try:
        profile_row = customer_profile[customer_profile['Заказчик'] == company]
        if not profile_row.empty:
            return jsonify({
                'любимый_тип_тс': profile_row['ЛюбимыйТипТС'].values[0],
                'исторический_любимый_тс': profile_row['ИсторическийЛюбимыйТС'].values[0],
                'любимый_статус_заказа': profile_row['ЛюбимыйСтатусЗаказа'].values[0],
                'среднее_пассажиров': float(orders_df[orders_df['Заказчик'] == company]['КоличествоПассажиров'].mean()),
                'всего_заказов': int(orders_df[orders_df['Заказчик'] == company].shape[0])
            })
        return jsonify({'error': 'Профиль не найден'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/<company>')
def get_history(company):
    try:
        history = orders_df[orders_df['Заказчик'] == company].sort_values(by='Date', ascending=False).head(3)
        rows = []
        for _, row in history.iterrows():
            rows.append({
                'дата': str(row.get('Date', '')),
                'тип_тс': row.get('ТипТС', ''),
                'пассажиров': int(row.get('КоличествоПассажиров', 0)),
                'цена': int(row.get('ЦенаЗаЧас', 0)),
                'тип': row.get('ТипЗаказа', ''),
                'статус': row.get('СтатусЗаказа', ''),
                'маршрут': f"{row.get('ЗагрузкаПункт', '')} → {row.get('РазгрузкаПункт', '')}"
            })
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommend', methods=['POST'])
def recommend():
    try:
        data = request.json
        заказчик = data['company']
        количество_пассажиров = int(data['passengers'])
        цена_за_час = int(data['price'])
        тип_заказа = data['status']

        profile_row = customer_profile[customer_profile['Заказчик'] == заказчик]
        любимый_тип_тс = profile_row['ЛюбимыйТипТС'].values[0] if not profile_row.empty else 'Неизвестно'
        исторический_любимый_тс = profile_row['ИсторическийЛюбимыйТС'].values[0] if not profile_row.empty else 'Неизвестно'
        любимый_статус_заказа = profile_row['ЛюбимыйСтатусЗаказа'].values[0] if not profile_row.empty else 'Неизвестно'

        input_data = pd.DataFrame([{
            'Заказчик': заказчик,
            'КоличествоПассажиров': количество_пассажиров,
            'ЦенаЗаЧас': цена_за_час,
            'ТипЗаказа': тип_заказа,
            'ЛюбимыйТипТС': любимый_тип_тс,
            'ИсторическийЛюбимыйТС': исторический_любимый_тс,
            'ЛюбимыйСтатусЗаказа': любимый_статус_заказа
        }])

        pool = Pool(input_data, cat_features=['Заказчик', 'ТипЗаказа', 'ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа'])
        probs = model.predict_proba(pool)[0]
        top_indices = probs.argsort()[-10:][::-1]

        def define_range(passengers):
            if passengers <= 4: return (1, 4)
            elif passengers <= 8: return (5, 8)
            elif passengers <= 20: return (9, 20)
            elif passengers <= 50: return (21, 50)
            else: return (51, 100)

        min_capacity, max_capacity = define_range(количество_пассажиров)
        recommendations = []

        for idx in top_indices:
            ref = model.classes_[idx]
            probability = probs[idx]
            capacity = type_ts_mapping.get(ref, 999)
            if min_capacity <= capacity <= max_capacity:
                recommendations.append({
                    'type': ref,
                    'probability': float(probability),
                    'capacity': int(capacity)
                })
            if len(recommendations) == 3:
                break

        return jsonify(recommendations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/save_order', methods=['POST'])
def save_order():
    try:
        data = request.json

        vehicle_type = data.get('vehicle_type')
        start_str = data.get('booking_start')
        end_str = data.get('booking_end')

        if not vehicle_type or not start_str or not end_str:
            return jsonify({'error': 'Недостаточно данных для проверки автопарка'}), 400

        # Преобразуем строки в datetime
        start = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
        available_count = fleet_info.get(vehicle_type, 1)

        # Загружаем заказы из Google Sheets
        orders_data = sheet.get_all_records()
        df = pd.DataFrame(orders_data)

        # Преобразуем колонки с датами в datetime
        df['ДатаБрони'] = pd.to_datetime(df['ДатаБрони'], format="%Y-%m-%d %H:%M:%S", errors='coerce')
        df['ОкончаниеБрони'] = pd.to_datetime(df['ОкончаниеБрони'], format="%Y-%m-%d %H:%M:%S", errors='coerce')

        # Фильтруем пересекающиеся заказы
        overlapping = df[
            (df['ТипТС'] == vehicle_type) &
            (df['ДатаБрони'] <= end) &
            (df['ОкончаниеБрони'] >= start)
        ]

        if len(overlapping) >= available_count:
            return jsonify({'error': f'Все {available_count} {vehicle_type} уже забронированы на это время.'}), 409

        # Сохраняем заказ
        save_order_data(data)
        return jsonify({'status': 'ok'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/view_orders')
def view_orders():
    try:
        records = sheet.get_all_records()
        return jsonify(records)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download_orders')
def download_orders():
    return jsonify({'error': 'Функция выгрузки отключена при использовании Google Sheets.'}), 501



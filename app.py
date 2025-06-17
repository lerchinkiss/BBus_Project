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
    fleet_info = {k.strip().lower(): v for k, v in fleet_info.items()}
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
        start_str = data.get("booking_start")
        end_str = data.get("booking_end")

        start = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S") if start_str else None
        end = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S") if end_str else None

        profile_row = customer_profile[customer_profile['Заказчик'] == заказчик]
        любимый_тип_тс = profile_row['ЛюбимыйТипТС'].values[0] if not profile_row.empty else None
        исторический_любимый_тс = profile_row['ИсторическийЛюбимыйТС'].values[0] if not profile_row.empty else 'Неизвестно'
        любимый_статус_заказа = profile_row['ЛюбимыйСтатусЗаказа'].values[0] if not profile_row.empty else 'Неизвестно'

        input_data = pd.DataFrame([{
            'Заказчик': заказчик,
            'КоличествоПассажиров': количество_пассажиров,
            'ЦенаЗаЧас': цена_за_час,
            'ТипЗаказа': тип_заказа,
            'ЛюбимыйТипТС': любимый_тип_тс or 'Неизвестно',
            'ИсторическийЛюбимыйТС': исторический_любимый_тс,
            'ЛюбимыйСтатусЗаказа': любимый_статус_заказа
        }])

        pool = Pool(input_data, cat_features=[
            'Заказчик', 'ТипЗаказа', 'ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа'
        ])
        probs = model.predict_proba(pool)[0]
        model_classes = list(model.classes_)

        def define_range(passengers):
            if passengers <= 4: return (1, 4)
            elif passengers <= 7: return (5, 7)
            elif passengers <= 16: return (8, 16)
            elif passengers <= 20: return (17, 20)
            elif passengers <= 35: return (21, 35)
            elif passengers <= 43: return (36, 43)
            elif passengers <= 49: return (44, 49)
            elif passengers <= 53: return (50, 53)
            elif passengers <= 59: return (54, 59)
            else: return (60, 100)

        min_cap, max_cap = define_range(количество_пассажиров)

        df = pd.DataFrame(sheet.get_all_records())
        df['ТипТС'] = df['ТипТС'].astype(str).str.strip().str.lower()

        def is_available(ts_type):
            ts_type_clean = ts_type.strip().lower()
            count = fleet_info.get(ts_type_clean, 1)
            if not start or not end:
                return True
            overlapping = df[
                (df['ТипТС'] == ts_type_clean) &
                (pd.to_datetime(df['ДатаБрони']) < end) &
                (pd.to_datetime(df['ОкончаниеБрони']) > start)
            ]
            return len(overlapping) < count

        # Проверяем, есть ли похожие заказы у этого заказчика
        company_orders = orders_df[orders_df['Заказчик'] == заказчик]
        has_similar = not company_orders[
            (company_orders['КоличествоПассажиров'].between(количество_пассажиров - 1, количество_пассажиров + 1)) &
            (company_orders['ЦенаЗаЧас'].between(цена_за_час * 0.8, цена_за_час * 1.2))
        ].empty

        if not has_similar:
            print("Используем вероятности по похожим заказам других клиентов.")

            def estimate_from_similar_orders(passengers, price):
                delta_passengers = max(2, int(passengers * 0.15))  # Гибкий диапазон
                delta_price = 0.2  # 20%

                lower_p = passengers - delta_passengers
                upper_p = passengers + delta_passengers
                lower_price = price * (1 - delta_price)
                upper_price = price * (1 + delta_price)

                similar = orders_df[
                    (orders_df['КоличествоПассажиров'].between(lower_p, upper_p)) &
                    (orders_df['ЦенаЗаЧас'].between(lower_price, upper_price))
                    ]

                if similar.empty:
                    return {cls: 0.05 for cls in model_classes}  # каждому по минимуму

                total = len(similar)
                counts = similar['ТипТС'].value_counts()
                return {cls: round(counts.get(cls, 0) / total, 3) for cls in model_classes}

            similar_probs = estimate_from_similar_orders(количество_пассажиров, цена_за_час)
            probs = [similar_probs.get(cls, 0.0) for cls in model_classes]

        top_indices = sorted(range(len(probs)), key=lambda i: probs[i], reverse=True)

        recommendations = []
        added_types = set()

        # Любимый ТС
        if любимый_тип_тс and любимый_тип_тс != 'Неизвестно':
            capacity = type_ts_mapping.get(любимый_тип_тс, 999)
            recommendations.append({
                'type': любимый_тип_тс,
                'capacity': int(capacity),
                'probability': 1.0,
                'preferred': True,
                'valid_capacity': min_cap <= capacity <= max_cap,
                'available': is_available(любимый_тип_тс)
            })
            added_types.add(любимый_тип_тс)

        # Модельные рекомендации
        for idx in top_indices:
            ref = model_classes[idx]
            if ref in added_types:
                continue
            capacity = type_ts_mapping.get(ref, 999)
            if not (min_cap <= capacity <= max_cap):
                continue
            recommendations.append({
                'type': ref,
                'capacity': int(capacity),
                'probability': float(probs[idx]),
                'preferred': False,
                'valid_capacity': True,
                'available': is_available(ref)
            })
            added_types.add(ref)

        # Остальные подходящие по вместимости
        for ref, capacity in type_ts_mapping.items():
            if ref in added_types:
                continue
            if min_cap <= capacity <= max_cap:
                recommendations.append({
                    'type': ref,
                    'capacity': int(capacity),
                    'probability': 0.0,
                    'preferred': False,
                    'valid_capacity': True,
                    'available': is_available(ref)
                })

        return jsonify(recommendations)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notify_request', methods=['POST'])
def notify_request():
    try:
        data = request.json
        company = data.get("company")
        vehicle_type = data.get("vehicle_type")
        desired_time = data.get("desired_time")
        contact = data.get("contact")

        row = [
            company,
            vehicle_type,
            desired_time,
            contact,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        sheet_notify.append_row(row)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/save_order', methods=['POST'])
def save_order():
    try:
        data = request.json
        print("Получены данные заказа:", data)

        vehicle_type_original = data.get('vehicle_type', '').strip()
        vehicle_type_clean = vehicle_type_original.lower()
        start_str = data.get('booking_start')
        end_str = data.get('booking_end')

        # Преобразуем строки в datetime
        start = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")

        # Валидации
        if int(data.get("passengers", 0)) < 1 or int(data.get("passengers", 0)) > 59:
            return jsonify({'error': 'Недопустимое количество пассажиров'}), 400

        if float(data.get("price", 0)) <= 0:
            return jsonify({'error': 'Стоимость должна быть положительной'}), 400

        if not data.get("route_from") or not data.get("route_to"):
            return jsonify({'error': 'Маршруты ОТ и ДО обязательны'}), 400

        # Проверка занятости ТС
        if vehicle_type_original:
            vehicle_type_clean = vehicle_type_original.strip().lower()
            available_count = fleet_info.get(vehicle_type_clean, 1)
            print(f"Тип ТС: {vehicle_type_clean}, Доступно машин: {available_count}")

            df = pd.DataFrame(sheet.get_all_records())
            df['ТипТС'] = df['ТипТС'].astype(str).str.strip().str.lower()
            df['ДатаБрони'] = pd.to_datetime(df['ДатаБрони'], errors='coerce')
            df['ОкончаниеБрони'] = pd.to_datetime(df['ОкончаниеБрони'], errors='coerce')

            overlapping = df[
                (df['ТипТС'] == vehicle_type_clean) &
                ((df['ДатаБрони'] <= end) & (df['ОкончаниеБрони'] >= start))
            ]

            print(f"Найдено пересекающихся заказов: {len(overlapping)}")

            if len(overlapping) >= available_count:
                return jsonify({'error': f'Все {available_count} {vehicle_type_original} уже забронированы на это время.'}), 409

        # Сохраняем заказ в таблицу
        save_order_data(data)
        return jsonify({'status': 'ok'})

    except Exception as e:
        print(f"Ошибка при сохранении заказа: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/view_orders')
def view_orders():
    try:
        records = sheet.get_all_records()
        return jsonify(records)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/analysis_data')
def get_analysis_data():
    try:
        # Топ типов ТС
        top_vehicles = orders_df['ТипТС'].value_counts().head(10).reset_index()
        top_vehicles.columns = ['type', 'count']
        top_vehicles = top_vehicles.to_dict('records')

        # Топ заказчиков
        top_customers = orders_df['Заказчик'].value_counts().head(10).reset_index()
        top_customers.columns = ['customer', 'count']
        top_customers = top_customers.to_dict('records')

        # Топ-10 заказчиков по пассажирам
        passengers_by_customer = orders_df.groupby('Заказчик')['КоличествоПассажиров'].sum().reset_index()
        passengers_by_customer.columns = ['customer', 'total_passengers']
        passengers_by_customer = passengers_by_customer.sort_values('total_passengers', ascending=False).head(10)
        passengers_by_customer = passengers_by_customer.to_dict('records')

        # Распределение вместимости ТС
        capacity_distribution = orders_df['КоличествоПассажиров'].value_counts().reset_index()
        capacity_distribution.columns = ['capacity', 'count']
        capacity_distribution = capacity_distribution.to_dict('records')

        # Топ-10 ТС по вместимости
        top_vehicles_by_capacity = orders_df.groupby('ТипТС')['КоличествоПассажиров'].max().reset_index()
        top_vehicles_by_capacity.columns = ['type', 'capacity']
        top_vehicles_by_capacity = top_vehicles_by_capacity.sort_values('capacity', ascending=False).head(10)
        top_vehicles_by_capacity = top_vehicles_by_capacity.to_dict('records')

        # Распределение цен по типам ТС
        price_distribution = orders_df[['ТипТС', 'ЦенаЗаЧас']].dropna().to_dict('records')

        # Динамика заказов по месяцам
        orders_df['Месяц'] = pd.to_datetime(orders_df['Date']).dt.strftime('%Y-%m')
        monthly_orders = orders_df.groupby('Месяц').size().reset_index()
        monthly_orders.columns = ['month', 'count']
        monthly_orders = monthly_orders.to_dict('records')

        # Диапазон цен по типам ТС
        price_range = orders_df.groupby('ТипТС').agg({
            'ЦенаЗаЧас': ['min', 'max']
        }).reset_index()
        price_range.columns = ['type', 'min_price', 'max_price']
        price_range = price_range.to_dict('records')

        return jsonify({
            'topVehicles': top_vehicles,
            'topCustomers': top_customers,
            'passengersByCustomer': passengers_by_customer,
            'capacityDistribution': capacity_distribution,
            'topVehiclesByCapacity': top_vehicles_by_capacity,
            'priceDistribution': price_distribution,
            'monthlyOrders': monthly_orders,
            'priceRange': price_range
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download_orders')
def download_orders():
    return jsonify({'error': 'Функция выгрузки отключена при использовании Google Sheets.'}), 501
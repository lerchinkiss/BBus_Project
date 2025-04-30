from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import os
from catboost import CatBoostClassifier, Pool
from link_tables import apply_links
import pickle
import time

app = Flask(__name__, static_folder='site')
CORS(app)

CACHE_FILE = 'data_cache.pkl'
CACHE_TIMEOUT = 3600

def save_to_cache(data):
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

print("Загрузка модели...")
model = CatBoostClassifier()
model_path = os.path.abspath("models/catboost_typets_model_v3.cbm")
print("Загружаем модель из:", model_path)
model.load_model(model_path)

def load_data():
    print("Начинаем загрузку данных...")
    cached_data = load_from_cache()
    if cached_data is not None:
        print("Данные загружены из кэша")
        return cached_data

    try:
        orders_df = pd.read_excel(os.path.join("filtered_datasets", "bbOrders_filtered.xlsx"))
        orders_df = apply_links(orders_df)
        customer_profile = pd.read_excel(os.path.join("prepared_data", "customer_profile.xlsx"))
        type_ts_df = pd.read_excel(os.path.join("filtered_datasets", "uatTypeTS_filtered.xlsx"))
        type_ts_df = type_ts_df.dropna(subset=['Description', 'МаксМест'])
        type_ts_mapping = dict(zip(type_ts_df['Description'], type_ts_df['МаксМест']))
        data = (orders_df, customer_profile, type_ts_mapping)
        save_to_cache(data)
        return data
    except Exception as e:
        print(f"Ошибка при загрузке данных: {str(e)}")
        raise

orders_df, customer_profile, type_ts_mapping = load_data()

@app.route('/')
def index():
    return send_from_directory('site', 'index.html')

@app.route('/api/companies')
def get_companies():
    try:
        unique_companies = orders_df['Заказчик'].dropna().unique().tolist()
        unique_companies.sort()
        return jsonify(unique_companies)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/customer_profile/<company>')
def get_customer_profile(company):
    try:
        profile_row = customer_profile[customer_profile['Заказчик'] == company]
        if not profile_row.empty:
            profile = {
                'любимый_тип_тс': profile_row['ЛюбимыйТипТС'].values[0],
                'исторический_любимый_тс': profile_row['ИсторическийЛюбимыйТС'].values[0],
                'любимый_статус_заказа': profile_row['ЛюбимыйСтатусЗаказа'].values[0],
                'среднее_пассажиров': float(orders_df[orders_df['Заказчик'] == company]['КоличествоПассажиров'].mean()),
                'всего_заказов': int(orders_df[orders_df['Заказчик'] == company].shape[0])
            }
            return jsonify(profile)
        return jsonify({'error': 'Профиль не найден'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/<company>')
def get_history(company):
    try:
        history = orders_df[orders_df['Заказчик'] == company].sort_values(by='ДатаСоздания', ascending=False).head(3)
        rows = []
        for _, row in history.iterrows():
            rows.append({
                'дата': str(row.get('ДатаСоздания', '')),
                'тип_тс': row.get('ТипТС', ''),
                'пассажиров': int(row.get('КоличествоПассажиров', 0)),
                'цена': int(row.get('ЦенаЗаЧас', 0)),
                'тип': row.get('ТипЗаказа', ''),
                'статус': row.get('СтатусЗаказа', ''),
                'маршрут': f"{row.get('ПунктЗагрузки', '')} → {row.get('ПунктРазгрузки', '')}"
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
        if not profile_row.empty:
            любимый_тип_тс = profile_row['ЛюбимыйТипТС'].values[0]
            исторический_любимый_тс = profile_row['ИсторическийЛюбимыйТС'].values[0]
            любимый_статус_заказа = profile_row['ЛюбимыйСтатусЗаказа'].values[0]
        else:
            любимый_тип_тс = 'Неизвестно'
            исторический_любимый_тс = 'Неизвестно'
            любимый_статус_заказа = 'Неизвестно'

        input_data = pd.DataFrame([{
            'Заказчик': заказчик,
            'КоличествоПассажиров': количество_пассажиров,
            'ЦенаЗаЧас': цена_за_час,
            'ТипЗаказа': тип_заказа,
            'ЛюбимыйТипТС': любимый_тип_тс,
            'ИсторическийЛюбимыйТС': исторический_любимый_тс,
            'ЛюбимыйСтатусЗаказа': любимый_статус_заказа
        }])

        pool = Pool(input_data,
                    cat_features=['Заказчик', 'ТипЗаказа', 'ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа'])

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

        historical_matches = orders_df[
            (orders_df['КоличествоПассажиров'] >= min_capacity) &
            (orders_df['КоличествоПассажиров'] <= max_capacity)
        ]
        if not historical_matches.empty:
            top_historical = historical_matches['ТипТС'].value_counts().head(3).index.tolist()
            for ref in top_historical:
                if all(r['type'] != ref for r in recommendations):
                    capacity = type_ts_mapping.get(ref, 999)
                    recommendations.append({
                        'type': ref,
                        'probability': 0.0,
                        'capacity': int(capacity)
                    })
                    if len(recommendations) == 3:
                        break

        return jsonify(recommendations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import os
from catboost import CatBoostClassifier, Pool
from link_tables import apply_links
import pickle
import time

app = Flask(__name__, static_folder='site')

CACHE_FILE = 'data_cache.pkl'
CACHE_TIMEOUT = 3600  # 1 час

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

# === Загрузка модели ===
print("Загрузка модели...")
model = CatBoostClassifier()
model_path = os.path.abspath("models/catboost_typets_model_v3.cbm")
print("Загружаем модель из:", model_path)
model.load_model(model_path)

# === Загрузка данных ===
def load_data():
    print("Начинаем загрузку данных...")
    
    # Пробуем загрузить из кэша
    cached_data = load_from_cache()
    if cached_data is not None:
        print("Данные загружены из кэша")
        return cached_data

    try:
        print("Загружаем orders_df...")
        orders_df = pd.read_excel(os.path.join("filtered_datasets", "bbOrders_filtered.xlsx"))
        print(f"Загружено {len(orders_df)} заказов")
        
        print("Применяем связи...")
        orders_df = apply_links(orders_df)
        print("Связи применены")
        
        print("Загружаем customer_profile...")
        customer_profile = pd.read_excel(os.path.join("prepared_data", "customer_profile.xlsx"))
        print(f"Загружено {len(customer_profile)} профилей клиентов")
        
        print("Загружаем type_ts_df...")
        type_ts_df = pd.read_excel(os.path.join("filtered_datasets", "uatTypeTS_filtered.xlsx"))
        print(f"Загружено {len(type_ts_df)} типов ТС")
        
        type_ts_df = type_ts_df.dropna(subset=['Description', 'МаксМест'])
        type_ts_mapping = dict(zip(type_ts_df['Description'], type_ts_df['МаксМест']))
        print(f"Создан mapping для {len(type_ts_mapping)} типов ТС")
        
        data = (orders_df, customer_profile, type_ts_mapping)
        save_to_cache(data)
        return data
    except Exception as e:
        print(f"Ошибка при загрузке данных: {str(e)}")
        raise

print("Загрузка данных...")
orders_df, customer_profile, type_ts_mapping = load_data()
print("Данные загружены")

@app.route('/')
def index():
    return send_from_directory('site', 'index.html')

@app.route('/api/companies')
def get_companies():
    try:
        unique_companies = sorted(orders_df['Заказчик'].dropna().unique().tolist())
        print(f"Получен список компаний: {len(unique_companies)} компаний")
        return jsonify(unique_companies)
    except Exception as e:
        print(f"Ошибка при получении списка компаний: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/customer_profile/<company>')
def get_customer_profile(company):
    try:
        print(f"Запрошен профиль для компании: {company}")
        profile_row = customer_profile[customer_profile['Заказчик'] == company]
        
        if not profile_row.empty:
            profile = {
                'любимый_тип_тс': profile_row['ЛюбимыйТипТС'].values[0],
                'исторический_любимый_тс': profile_row['ИсторическийЛюбимыйТС'].values[0],
                'любимый_статус_заказа': profile_row['ЛюбимыйСтатусЗаказа'].values[0],
                'среднее_пассажиров': float(orders_df[orders_df['Заказчик'] == company]['КоличествоПассажиров'].mean()),
                'всего_заказов': int(orders_df[orders_df['Заказчик'] == company].shape[0])
            }
            print(f"Профиль найден: {profile}")
            return jsonify(profile)
        print("Профиль не найден")
        return jsonify({'error': 'Профиль не найден'})
    except Exception as e:
        print(f"Ошибка при получении профиля: {str(e)}")
        return jsonify({'error': str(e)}), 500

def define_range(passengers):
    if passengers <= 4:
        return (1, 4)
    elif passengers <= 8:
        return (5, 8)
    elif passengers <= 20:
        return (9, 20)
    elif passengers <= 50:
        return (21, 50)
    else:
        return (51, 100)

@app.route('/api/recommend', methods=['POST'])
def recommend():
    try:
        data = request.json
        print(f"Получены данные для рекомендации: {data}")
        
        заказчик = data['company']
        количество_пассажиров = int(data['passengers'])
        цена_за_час = int(data['price'])
        тип_заказа = data['status']

        print(f"Ищем профиль заказчика: {заказчик}")
        profile_row = customer_profile[customer_profile['Заказчик'] == заказчик]

        if not profile_row.empty:
            любимый_тип_тс = profile_row['ЛюбимыйТипТС'].values[0]
            исторический_любимый_тс = profile_row['ИсторическийЛюбимыйТС'].values[0]
            любимый_статус_заказа = profile_row['ЛюбимыйСтатусЗаказа'].values[0]
        else:
            любимый_тип_тс = 'Неизвестно'
            исторический_любимый_тс = 'Неизвестно'
            любимый_статус_заказа = 'Неизвестно'

        print("Формируем данные для предсказания")
        input_data = pd.DataFrame([{
            'Заказчик': заказчик,
            'КоличествоПассажиров': количество_пассажиров,
            'ЦенаЗаЧас': цена_за_час,
            'ТипЗаказа': тип_заказа,
            'ЛюбимыйТипТС': любимый_тип_тс,
            'ИсторическийЛюбимыйТС': исторический_любимый_тс,
            'ЛюбимыйСтатусЗаказа': любимый_статус_заказа
        }])

        print("Создаем Pool для предсказания")
        pool = Pool(input_data,
                    cat_features=['Заказчик', 'ТипЗаказа', 'ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа'])

        print("Делаем предсказание")
        probs = model.predict_proba(pool)[0]
        top_indices = probs.argsort()[-10:][::-1]

        min_capacity, max_capacity = define_range(количество_пассажиров)
        print(f"Диапазон вместимости: {min_capacity}-{max_capacity}")
        
        recommendations = []

        print("Формируем рекомендации")
        for idx in top_indices:
            ref = model.classes_[idx]
            probability = probs[idx]
            capacity = type_ts_mapping.get(ref, 999)
            print(f"Проверяем: {ref} (вместимость: {capacity})")

            if min_capacity <= capacity <= max_capacity:
                recommendations.append({
                    'type': ref,
                    'probability': float(probability),
                    'capacity': int(capacity)
                })
                print(f"Добавлена рекомендация: {ref}")

            if len(recommendations) == 3:
                break

        print("Ищем исторические совпадения")
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
                    print(f"Добавлена историческая рекомендация: {ref}")
                    if len(recommendations) == 3:
                        break

        print(f"Итоговые рекомендации: {recommendations}")
        return jsonify(recommendations)
    except Exception as e:
        print(f"Ошибка при формировании рекомендаций: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
import os
from bs4 import BeautifulSoup
import requests
import pandas as pd
import warnings

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# Функция для извлечения данных с одной страницы
def extract_bus_data(url):
    try:
        response = requests.get(url, verify=False, timeout=10)  # Отключаем проверку сертификата
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Извлечение заголовка страницы - название транспорта
            title = soup.title.string.strip()
            bus_name = title.split("Трансфер и аренда")[1].strip() if "Трансфер и аренда" in title else title
            bus_name = clean_bus_name(bus_name)

            # Извлечение характеристик
            details = {"Название транспорта": bus_name}
            ul = soup.find('ul', class_='ul-horizontal-auto')
            if ul:
                for li in ul.find_all('li'):
                    key = li.text.split(":")[0].strip()
                    value = li.find('span').text.strip()
                    details[key] = value

            # Извлечение таблицы цен на аренду
            rent_table = []
            rent_section = soup.find('table', class_='table-price')
            if rent_section:
                rows = rent_section.find_all('tr')[2:]
                for row in rows:
                    cols = row.find_all('td')
                    rent_table.append({
                        "Название транспорта": bus_name,
                        "Аренда по городу (руб/час)": cols[0].text.strip(),
                        "Выезд за город (руб/км)": cols[1].text.strip(),
                        "Минимальное время аренды + подача": cols[2].text.strip(),
                        "Минимальное время аренды на свадьбу + подача": cols[3].text.strip()
                    })

            # Извлечение таблицы трансфера
            transfer_table = []
            transfer_section = soup.find("div", class_="transfer")
            if transfer_section:
                transfer_table_html = transfer_section.find("table", class_="table-price")
                if transfer_table_html:
                    rows = transfer_table_html.find_all("tr")[2:]
                    for row in rows:
                        cols = row.find_all('td')
                        transfer_table.append({
                            "Название транспорта": bus_name,
                            "Пункт назначения": cols[0].text.strip(),
                            "Стоимость трансфера (вс-чт)": cols[1].text.strip(),
                            "Стоимость трансфера (пт-сб)": cols[2].text.strip()
                        })

            return details, rent_table, transfer_table
        else:
            print(f"Ошибка HTTP {response.status_code} для {url}")
    except requests.exceptions.SSLError:
        print(f"Ошибка SSL при подключении к {url}")
    except requests.exceptions.RequestException as e:
        print(f"Общая ошибка подключения к {url}: {e}")
    return None, None, None


# Функция для корректировки названия транспорта
def clean_bus_name(name):
    words_to_remove = ["автобуса", "городского автобуса", "городского", "микро", "минивэна", "автомобиля"]
    for word in words_to_remove:
        name = name.replace(word, "").strip()
    return name


# Список URL-адресов
urls = [
    # Туристические автобусы
    "https://bbus.ru/catalog/yutong-6938-39-mest",
    "https://bbus.ru/catalog/yutong-6122-51-mesto",
    "https://bbus.ru/catalog/yutong-6122-53-mesta",
    "https://bbus.ru/catalog/yutong-6128-53-mesta",
    "https://bbus.ru/catalog/yutong-6122-49-mest-s-tualetom",
    "https://bbus.ru/catalog/yutong-6121-64-mesta",
    "https://bbus.ru/catalog/yutong-6127-55-mest",
    "https://bbus.ru/catalog/yutong-6128-51-mesto-s-tualetom",
    "https://bbus.ru/catalog/scania-touring-51-mesto",
    "https://bbus.ru/catalog/scania-touring-49-mest-s-tualetom",
    # Городские автобусы
    "https://bbus.ru/catalog/paz-vektor-nekst-25-41-mesto",
    "https://bbus.ru/catalog/paz-vektor-next-30",
    # Микроавтобусы
    "https://bbus.ru/catalog/mb-sprinter-w907-vip-19-mest",
    "https://bbus.ru/catalog/mb-sprinter-w907-16-mest",
    "https://bbus.ru/catalog/mb-sprinter-w907-19-mest",
    "https://bbus.ru/catalog/mb-sprinter-w906-15-4-mest",
    "https://bbus.ru/catalog/toyota-hiace-9-12-mest",
    "https://bbus.ru/catalog/gazel-next-19-mest",
    "https://bbus.ru/catalog/ford-transit",
    "https://bbus.ru/catalog/mb-sprint-gruz-pass",
    "https://bbus.ru/catalog/mb-sprinter-furgon-2-mesta",
    # Минивэны
    "https://bbus.ru/catalog/mercedes-benz-vito-7-mest",
    "https://bbus.ru/catalog/gac-gn8-6-mest",
    "https://bbus.ru/catalog/mercedes-benz-v-class",
    "https://bbus.ru/catalog/toyota-alphard-5-mest",
    "https://bbus.ru/catalog/volkswagen-caravelle-7-mest",
    "https://bbus.ru/catalog/hongqi-hq9",
    # Легковые автомобили
    "https://bbus.ru/catalog/toyota-camry-3-mesta",
    "https://bbus.ru/catalog/mercedes-benz-e-213",
    "https://bbus.ru/catalog/mercedes-benz-s-222",
    "https://bbus.ru/catalog/mercedes-benz-s-223",
    "https://bbus.ru/catalog/mercedes-maybach-s-class",
    "https://bbus.ru/catalog/hongqi-h5",
    "https://bbus.ru/catalog/hongqi-h9",
    "https://bbus.ru/catalog/moskvich-6",
    "https://bbus.ru/catalog/hyundai-sonata",
    "https://bbus.ru/catalog/kia-k900",
    "https://bbus.ru/catalog/genesis-g80",
    "https://bbus.ru/catalog/genesis-g90",
    "https://bbus.ru/catalog/hongqi-hq9",
    "https://bbus.ru/catalog/gac-gn8-6-mest"]

datasets_folder = "datasets"
if not os.path.exists(datasets_folder):
    os.makedirs(datasets_folder)

# Сбор данных
all_details = []
all_rent_prices = []
all_transfer_prices = []

for url in urls:
    print(f"Обработка: {url}")
    details, rent_table, transfer_table = extract_bus_data(url)
    if details:
        all_details.append(details)
    if rent_table:
        all_rent_prices.extend(rent_table)
    if transfer_table:
        all_transfer_prices.extend(transfer_table)

# Создание DataFrame
df_details = pd.DataFrame(all_details)
df_rent = pd.DataFrame(all_rent_prices)
df_transfer = pd.DataFrame(all_transfer_prices)

# Сохранение файлов в формате UTF-8 с BOM
def save_csv_with_bom(df, filename):
    output_path = os.path.join(datasets_folder, filename)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Файл сохранён: {output_path}")

save_csv_with_bom(df_details, "bus_details.csv")
save_csv_with_bom(df_rent, "rent_prices.csv")
save_csv_with_bom(df_transfer, "transfer_prices.csv")

print("Данные успешно сохранены.")

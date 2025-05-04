import matplotlib.pyplot as plt
import seaborn as sns

# Импортируем link_tables.py
from link_tables import *

# Загружаем датасет и применяем расшифровку
file_path = os.path.join("filtered_datasets", "bbOrders_filtered.xlsx")
df = pd.read_excel(file_path)
df = apply_links(df)

# Настройка стиля графиков
plt.style.use('seaborn')
sns.set_palette("husl")

print("Размер датафрейма:", df.shape)
print("\nТипы данных:")
print(df.dtypes)

#Пропущенные значения
print("\nПропущенные значения по колонкам:")
print(df.isnull().sum().sort_values(ascending=False))

#Базовая статистика по числовым полям
numeric_cols = ['ЦенаЗаЧас', 'ФактическаяСтоимость', 'РасчетнаяСтоимость', 'КоличествоПассажиров']
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        print(f"\nСтатистика по: {col}")
        print(df[col].describe())

#Анализ по заказчикам
plt.figure(figsize=(14, 6))
top_customers = df['Заказчик'].value_counts().head(10)
sns.barplot(x=top_customers.index, y=top_customers.values)
plt.title("Топ-10 заказчиков по количеству заказов")
plt.xlabel("Заказчик")
plt.ylabel("Количество заказов")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

#Анализ по типам ТС
plt.figure(figsize=(14, 6))
top_vehicle_types = df['ТипТС'].value_counts().head(10)
sns.barplot(x=top_vehicle_types.index, y=top_vehicle_types.values)
plt.title("Топ-10 типов ТС по количеству заказов")
plt.xlabel("Тип ТС")
plt.ylabel("Количество заказов")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

#Анализ по тарифам
plt.figure(figsize=(14, 6))
top_tariffs = df['Тариф'].value_counts().head(10)
sns.barplot(x=top_tariffs.index, y=top_tariffs.values)
plt.title("Топ-10 тарифов по количеству заказов")
plt.xlabel("Тариф")
plt.ylabel("Количество заказов")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

#Анализ по статусам заказов
plt.figure(figsize=(14, 6))
status_counts = df['СтатусЗаказа'].value_counts()
sns.barplot(x=status_counts.index, y=status_counts.values)
plt.title("Распределение заказов по статусам")
plt.xlabel("Статус заказа")
plt.ylabel("Количество заказов")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

#Анализ по ответственным
plt.figure(figsize=(14, 6))
top_responsible = df['Ответсвенный'].value_counts().head(10)
sns.barplot(x=top_responsible.index, y=top_responsible.values)
plt.title("Топ-10 ответственных по количеству заказов")
plt.xlabel("Ответственный")
plt.ylabel("Количество заказов")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

#Анализ стоимости
plt.figure(figsize=(14, 6))
sns.boxplot(x='ТипТС', y='ФактическаяСтоимость', data=df)
plt.title("Распределение фактической стоимости по типам ТС")
plt.xlabel("Тип ТС")
plt.ylabel("Фактическая стоимость")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

#Анализ по датам
if 'Date' in df.columns:
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.to_period('M')
    
    #Количество заказов по месяцам
    plt.figure(figsize=(14, 6))
    monthly_orders = df.groupby('Month').size()
    monthly_orders.plot(kind='line', marker='o')
    plt.title("Динамика количества заказов по месяцам")
    plt.xlabel("Месяц")
    plt.ylabel("Количество заказов")
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    
    #Средняя стоимость по месяцам
    plt.figure(figsize=(14, 6))
    monthly_cost = df.groupby('Month')['ФактическаяСтоимость'].mean()
    monthly_cost.plot(kind='line', marker='o')
    plt.title("Динамика средней стоимости заказов по месяцам")
    plt.xlabel("Месяц")
    plt.ylabel("Средняя стоимость")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

#Корреляционный анализ
numeric_cols = ['ЦенаЗаЧас', 'ФактическаяСтоимость', 'РасчетнаяСтоимость', 'КоличествоПассажиров']
plt.figure(figsize=(12, 8))
corr = df[numeric_cols].corr()
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", square=True)
plt.title("Корреляция между числовыми признаками")
plt.tight_layout()
plt.show()

#Анализ пассажиропотока
plt.figure(figsize=(14, 6))
sns.boxplot(x='ТипТС', y='КоличествоПассажиров', data=df)
plt.title("Распределение количества пассажиров по типам ТС")
plt.xlabel("Тип ТС")
plt.ylabel("Количество пассажиров")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

#Анализ по времени
plt.figure(figsize=(14, 6))
sns.boxplot(x='ТипТС', y='ВремяВПути', data=df)
plt.title("Распределение времени в пути по типам ТС")
plt.xlabel("Тип ТС")
plt.ylabel("Время в пути")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()




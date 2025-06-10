import matplotlib.pyplot as plt
import seaborn as sns
from common_imports import OUTPUTS_DIR

# Импортируем link_tables.py
from link_tables import *

# Загружаем датасет и применяем расшифровку
file_path = os.path.join("../..", "data", "filtered_datasets", "bbOrders_filtered.xlsx")
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

#Анализ по датам
if 'Date' in df.columns:
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.to_period('M')
    
    #Средняя стоимость по месяцам
    plt.figure(figsize=(14, 6))
    monthly_cost = df.groupby('Month')['ФактическаяСтоимость'].mean()
    monthly_cost.plot(kind='line', marker='o')
    plt.title("Динамика средней стоимости заказов по месяцам")
    plt.xlabel("Месяц")
    plt.ylabel("Средняя стоимость")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, 'monthly_cost_dynamics.png'))
    plt.show()

#Корреляционный анализ
numeric_cols = ['ЦенаЗаЧас', 'ФактическаяСтоимость', 'РасчетнаяСтоимость', 'КоличествоПассажиров']
plt.figure(figsize=(12, 8))
corr = df[numeric_cols].corr()
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", square=True)
plt.title("Корреляция между числовыми признаками")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUTS_DIR, 'correlation_matrix.png'))
plt.show()

#Анализ пассажиропотока
plt.figure(figsize=(14, 6))
sns.boxplot(x='ТипТС', y='КоличествоПассажиров', data=df)
plt.title("Распределение количества пассажиров по типам ТС")
plt.xlabel("Тип ТС")
plt.ylabel("Количество пассажиров")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUTS_DIR, 'passenger_distribution.png'))
plt.show()

#Анализ по времени
plt.figure(figsize=(14, 6))
sns.boxplot(x='ТипТС', y='ЧасыВодителю', data=df)
plt.title("Распределение времени в пути по типам ТС")
plt.xlabel("Тип ТС")
plt.ylabel("Время в пути")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUTS_DIR, 'travel_time_distribution.png'))
plt.show()




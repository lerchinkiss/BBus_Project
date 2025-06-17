import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from link_tables import apply_links
from common_imports import *

# Настройка стиля графиков
plt.style.use('seaborn')
sns.set_palette("husl")

# Отключаем интерактивный режим
# plt.ion()

class PlotManager:
    def __init__(self, root, df, df_models, custom_plots=None):
        self.root = root
        self.df = df
        self.df_models = df_models
        self.current_plot = 0
        if custom_plots is not None:
            self.plots = custom_plots
        else:
            self.plots = [
                self.create_top_vehicles_plot,
                self.create_top_customers_plot,
                self.create_passengers_by_customer_plot,
                self.create_capacity_distribution_plot,
                self.create_top_vehicles_by_capacity_plot,
                self.create_price_distribution_plot,
                self.create_monthly_orders_plot,
                self.create_price_range_plot,
                self.create_model_performance_plot
            ]
        
        # Создаем главный контейнер
        self.main_container = tk.Frame(root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Создаем фрейм для кнопок (фиксированный внизу)
        self.button_frame = tk.Frame(self.main_container)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Создаем кнопки
        self.prev_button = tk.Button(self.button_frame, text="← Предыдущий", command=self.show_previous)
        self.prev_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.next_button = tk.Button(self.button_frame, text="Следующий →", command=self.show_next)
        self.next_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        self.close_button = tk.Button(self.button_frame, text="Закрыть", command=self.close)
        self.close_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Создаем фрейм для графика с прокруткой
        self.plot_frame = tk.Frame(self.main_container)
        self.plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Создаем холст для прокрутки
        self.canvas_frame = tk.Canvas(self.plot_frame)
        self.scrollbar = tk.Scrollbar(self.plot_frame, orient="vertical", command=self.canvas_frame.yview)
        self.scrollable_frame = tk.Frame(self.canvas_frame)
        
        # Настраиваем прокрутку
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas_frame.configure(
                scrollregion=self.canvas_frame.bbox("all")
            )
        )
        
        self.canvas_frame.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas_frame.configure(yscrollcommand=self.scrollbar.set)
        
        # Размещаем элементы прокрутки
        self.canvas_frame.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Инициализируем переменные для хранения текущего графика
        self.canvas = None
        self.toolbar = None
        
        # Показываем первый график
        self.show_current()
    
    def show_current(self):
        """Показывает текущий график"""
        # Очищаем предыдущий график
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        if self.toolbar:
            self.toolbar.destroy()
        
        # Создаем новый график
        fig = self.plots[self.current_plot]()
        
        # Создаем canvas для графика
        self.canvas = FigureCanvasTkAgg(fig, master=self.scrollable_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Добавляем панель инструментов
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.scrollable_frame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Закрываем фигуру matplotlib, чтобы не создавать лишних окон
        plt.close(fig)
        
        # Прокручиваем к началу
        self.canvas_frame.yview_moveto(0)
    
    def show_next(self):
        """Показывает следующий график"""
        self.current_plot = (self.current_plot + 1) % len(self.plots)
        self.show_current()
    
    def show_previous(self):
        """Показывает предыдущий график"""
        self.current_plot = (self.current_plot - 1) % len(self.plots)
        self.show_current()
    
    def close(self):
        """Закрывает только текущее окно"""
        self.root.destroy()
    
    def create_top_vehicles_plot(self):
        """Создает график топ-10 типов ТС"""
        fig, ax = plt.subplots(figsize=(10, 6))
        top_vehicle_types = self.df['ТипТС'].value_counts().head(10)
        sns.barplot(x=top_vehicle_types.index, y=top_vehicle_types.values, ax=ax)
        ax.set_title("Топ-10 типов ТС по заказам")
        ax.set_xlabel("Тип ТС")
        ax.set_ylabel("Количество заказов")
        ax.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUTS_DIR, 'top_vehicles.png'))
        plt.close(fig)
        return fig
    
    def create_top_customers_plot(self):
        """Создает график топ-10 заказчиков"""
        fig, ax = plt.subplots(figsize=(10, 6))
        top_customers = self.df['Заказчик'].value_counts().head(10)
        sns.barplot(x=top_customers.index, y=top_customers.values, ax=ax)
        ax.set_title("Топ-10 заказчиков")
        ax.set_xlabel("Заказчик")
        ax.set_ylabel("Количество заказов")
        ax.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUTS_DIR, 'top_customers.png'))
        plt.close(fig)
        return fig
    
    def create_passengers_by_customer_plot(self):
        """Создает график топ-10 заказчиков по пассажирам"""
        fig, ax = plt.subplots(figsize=(10, 6))
        passengers_by_customer = self.df.groupby('Заказчик')['КоличествоПассажиров'].sum().sort_values(ascending=False).head(10)
        sns.barplot(x=passengers_by_customer.index, y=passengers_by_customer.values, ax=ax)
        ax.set_title("Топ-10 заказчиков по пассажирам")
        ax.set_xlabel("Заказчик")
        ax.set_ylabel("Общее количество пассажиров")
        ax.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUTS_DIR, 'passengers_by_customer.png'))
        plt.close(fig)
        return fig
    
    def create_capacity_distribution_plot(self):
        """Создает график распределения вместимости ТС"""
        fig, ax = plt.subplots(figsize=(10, 6))
        capacity_data = self.df_models.groupby('ТипТС')['ВсегоМест'].max().sort_values(ascending=False)
        sns.histplot(data=capacity_data, bins=20, ax=ax)
        ax.set_title("Распределение вместимости ТС")
        ax.set_xlabel("Количество мест")
        ax.set_ylabel("Количество типов ТС")
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUTS_DIR, 'capacity_distribution.png'))
        plt.close(fig)
        return fig

    def create_top_vehicles_by_capacity_plot(self):
        """Создает график топ-10 ТС по вместимости"""
        df_type_ts = pd.read_excel(os.path.join(DATA_DIR, "filtered_datasets", "uatTypeTS_filtered.xlsx"))
        type_ts_mapping = dict(zip(df_type_ts['Ref'], df_type_ts['Description']))
        capacity_data = self.df_models.groupby('ТипТС')['ВсегоМест'].max().sort_values(ascending=False).head(10)
        capacity_data.index = capacity_data.index.map(lambda x: type_ts_mapping.get(x, x))
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x=capacity_data.index, y=capacity_data.values, ax=ax)
        ax.set_title("Топ-10 ТС по вместимости")
        ax.set_xlabel("Тип ТС")
        ax.set_ylabel("Количество мест")
        ax.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUTS_DIR, 'top_vehicles_by_capacity.png'))
        plt.close(fig)
        return fig
    
    def create_price_distribution_plot(self):
        # Топ-8 типов ТС по количеству заказов
        top_types = self.df['ТипТС'].value_counts().head(8).index
        data = self.df[self.df['ТипТС'].isin(top_types)]
        order = data.groupby('ТипТС')['ЦенаЗаЧас'].median().sort_values(ascending=False).index

        fig, axes = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={'width_ratios': [2, 1]})

        # Violinplot
        sns.violinplot(
            data=data, 
            y='ТипТС', 
            x='ЦенаЗаЧас', 
            ax=axes[0],
            order=order, 
            hue='ТипТС',
            legend=False,
            palette='Set2', 
            cut=0, 
            inner='quartile'
        )
        axes[0].set_title("Violinplot: распределение цен по топ-8 типам ТС")
        axes[0].set_xlabel("Цена за час")
        axes[0].set_ylabel("Тип ТС")
        axes[0].grid(True, axis='x', linestyle='--', alpha=0.7)

        # Barplot медиан
        medians = data.groupby('ТипТС')['ЦенаЗаЧас'].median().loc[order]
        sns.barplot(
            data=pd.DataFrame({'ТипТС': medians.index, 'ЦенаЗаЧас': medians.values}),
            y='ТипТС', 
            x='ЦенаЗаЧас', 
            ax=axes[1], 
            hue='ТипТС',
            legend=False,
            palette='Set2'
        )
        axes[1].set_title("Медианная цена по типу ТС")
        axes[1].set_xlabel("Медианная цена за час")
        axes[1].set_ylabel("")
        axes[1].grid(True, axis='x', linestyle='--', alpha=0.7)

        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUTS_DIR, 'price_distribution.png'))
        plt.close(fig)
        return fig
    
    def create_monthly_orders_plot(self):
        """Создает график динамики заказов"""
        fig, ax = plt.subplots(figsize=(10, 6))
        self.df['Месяц'] = self.df['Дата'].dt.to_period('M')
        monthly_orders = self.df.groupby('Месяц').size()
        monthly_orders.plot(kind='line', marker='o', ax=ax)
        ax.set_title("Динамика заказов по месяцам")
        ax.set_xlabel("Месяц")
        ax.set_ylabel("Количество заказов")
        ax.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUTS_DIR, 'monthly_orders.png'))
        plt.close(fig)
        return fig
    
    def create_price_range_plot(self):
        """Создает график диапазона цен"""
        fig, ax = plt.subplots(figsize=(12, 8))  # Увеличиваем размер графика
        price_ranges = self.df.groupby('ТипТС')['ЦенаЗаЧас'].agg(['min', 'max']).sort_values('max', ascending=False)
        price_ranges.plot(kind='bar', ax=ax)
        ax.set_title("Диапазон цен по типам ТС")
        ax.set_xlabel("Тип ТС")
        ax.set_ylabel("Цена за час")
        ax.tick_params(axis='x', rotation=90)  # Поворачиваем подписи на 90 градусов для лучшей читаемости
        ax.legend(['Минимальная цена', 'Максимальная цена'])
        plt.tight_layout()  # Автоматически настраиваем отступы
        plt.savefig(os.path.join(OUTPUTS_DIR, 'price_range.png'))
        plt.close(fig)
        return fig
    
    def create_model_performance_plot(self):
        """Создает график производительности модели"""
        # Загружаем модель
        model = CatBoostClassifier()
        model.load_model(os.path.join(MODELS_DIR, 'catboost_typets_model_v3.cbm'))
        
        # Получаем имена признаков из модели
        model_feature_names = model.feature_names_
        
        # Подготавливаем данные для предсказания в точном порядке признаков модели
        X = pd.DataFrame()
        for feature in model_feature_names:
            if feature in self.df.columns:
                X[feature] = self.df[feature].fillna(self.df[feature].median())
            else:
                logger.warning(f"Признак {feature} отсутствует в данных")
                X[feature] = 0  # Заполняем нулями отсутствующие признаки
        
        y_true = self.df['ТипТС']
        
        # Создаем пул данных с точным порядком признаков
        pool = Pool(X[model_feature_names])
        
        # Делаем предсказания
        y_pred = model.predict(pool)
        
        # Создаем график с двумя подграфиками
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 1. Матрица ошибок
        cm = confusion_matrix(y_true, y_pred)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax1)
        ax1.set_title('Матрица ошибок')
        ax1.set_xlabel('Предсказанный тип ТС')
        ax1.set_ylabel('Истинный тип ТС')
        
        # 2. Распределение предсказаний
        pred_counts = pd.Series(y_pred).value_counts().head(10)
        sns.barplot(x=pred_counts.index, y=pred_counts.values, ax=ax2)
        ax2.set_title('Топ-10 предсказанных типов ТС')
        ax2.set_xlabel('Тип ТС')
        ax2.set_ylabel('Количество предсказаний')
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUTS_DIR, 'model_performance.png'))
        plt.close(fig)
        return fig

def load_and_prepare_data():
    """Загрузка и подготовка данных"""
    logger.info("Загрузка данных...")
    
    # Загрузка основных данных
    df_orders = pd.read_excel(os.path.join(DATA_DIR, "filtered_datasets", "bbOrders_filtered.xlsx"))
    df_models = pd.read_excel(os.path.join(DATA_DIR, "filtered_datasets", "uatModelsTS_filtered.xlsx"))
    df_type_ts = pd.read_excel(os.path.join(DATA_DIR, "filtered_datasets", "uatTypeTS_filtered.xlsx"))
    
    # Применяем расшифровку через link_tables
    df_orders = apply_links(df_orders)
    
    # Подготовка данных
    df_orders['Дата'] = pd.to_datetime(df_orders['Date'], errors='coerce')
    df_orders['Маршрут'] = df_orders['ЗагрузкаПункт'].astype(str) + " -> " + df_orders['РазгрузкаПункт'].astype(str)
    df_orders['КоличествоПассажиров'] = pd.to_numeric(df_orders['КоличествоПассажиров'], errors='coerce')
    
    return df_orders, df_models, df_type_ts

def analyze_orders(df, df_models):
    """Анализ заказов"""
    logger.info("\n===== Анализ заказов =====")
    
    # Базовая статистика
    logger.info("\nРазмер датафрейма: %s", df.shape)
    logger.info("\nТипы данных:")
    logger.info(df.dtypes)
    
    # Пропущенные значения
    logger.info("\nПропущенные значения по колонкам:")
    logger.info(df.isnull().sum().sort_values(ascending=False))
    
    # Статистика по числовым полям
    numeric_cols = ['ЦенаЗаЧас', 'ФактическаяСтоимость', 'РасчетнаяСтоимость', 'КоличествоПассажиров']
    for col in numeric_cols:
        if col in df.columns:
            logger.info(f"\nСтатистика по: {col}")
            logger.info(df[col].describe())

def analyze_customers(df):
    """Анализ клиентов"""
    logger.info("\n===== Анализ клиентов =====")
    
    # Топ маршрутов по заказчикам
    logger.info("\n--- Топ маршрутов по каждому заказчику ---")
    top_routes = (
        df.groupby(['Заказчик', 'Маршрут'])
        .size()
        .reset_index(name='Количество')
        .sort_values(['Заказчик', 'Количество'], ascending=[True, False])
    )
    most_common_routes = top_routes.groupby('Заказчик').first().reset_index()
    logger.info(most_common_routes.head(10))
    
    # Популярные ТС у заказчиков
    logger.info("\n--- Популярные ТС у заказчиков ---")
    top_ts = (
        df.groupby(['Заказчик', 'ТС'])
        .size()
        .reset_index(name='Частота')
        .sort_values(['Заказчик', 'Частота'], ascending=[True, False])
    )
    most_common_ts = top_ts.groupby('Заказчик').first().reset_index()
    logger.info(most_common_ts.head(10))
    
    # Среднее количество пассажиров
    logger.info("\n--- Среднее количество пассажиров ---")
    avg_passengers = df.groupby('Заказчик')['КоличествоПассажиров'].mean().round(1)
    logger.info(avg_passengers.head(10))

def analyze_vehicles(df, df_models, df_type_ts):
    """Анализ транспортных средств"""
    logger.info("\n===== Анализ транспортных средств =====")
    
    # Анализ заказов с "Not Information"
    not_info_orders = df[df['ТипТС'] == 'Not Information']
    logger.info("\nАнализ заказов с 'Not Information' в колонке ТипТС:")
    logger.info(f"Количество заказов с 'Not Information': {len(not_info_orders)}")
    logger.info(f"Процент от общего количества заказов: {len(not_info_orders)/len(df)*100:.2f}%")
    
    # Анализ цен по типам ТС
    logger.info("\n--- Анализ цен по типам ТС ---")
    price_analysis = df.groupby('ТипТС').agg({
        'ЦенаЗаЧас': ['min', 'max', 'mean', 'median', 'count']
    }).round(2)
    price_analysis.columns = ['МинимальнаяЦена', 'МаксимальнаяЦена', 'СредняяЦена', 'МедианнаяЦена', 'КоличествоЗаказов']
    logger.info(price_analysis.sort_values('КоличествоЗаказов', ascending=False))

def load_customer_profile():
    """Загрузка профиля заказчиков"""
    try:
        customer_profile = pd.read_excel(os.path.join(PREPARED_DATA_DIR, "customer_profile.xlsx"))
        return customer_profile
    except Exception as e:
        logger.error(f"\nОШИБКА: Не удалось загрузить профиль заказчиков: {str(e)}")
        logger.error("Проверьте наличие файла data/prepared_data/customer_profile.xlsx")
        return None

def test_model(df):
    """Тестирование модели"""
    logger.info("\n===== Тестирование модели =====")
    
    # Загружаем профиль заказчиков
    customer_profile = load_customer_profile()
    if customer_profile is None:
        return
    
    # Загружаем модель
    model_path = os.path.join(MODELS_DIR, "catboost_typets_model_v3.cbm")
    
    # Проверяем существование файла модели
    if not os.path.exists(model_path):
        logger.error(f"\nОШИБКА: Файл модели не найден по пути: {model_path}")
        logger.error("Проверьте, что:")
        logger.error("1. Файл модели находится в папке outputs/models/")
        logger.error("2. Имя файла точно соответствует: catboost_typets_model_v3.cbm")
        return
    
    logger.info(f"\nЗагрузка модели из: {model_path}")
    model = CatBoostClassifier()
    model.load_model(model_path)
    
    # Объединяем данные с профилем заказчиков
    df = df.merge(customer_profile, on='Заказчик', how='left')
    
    # Определяем категориальные признаки
    cat_features = ['Заказчик', 'ТипЗаказа', 'ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа']
    
    # Подготавливаем данные
    X = df[['Заказчик', 'КоличествоПассажиров', 'ЦенаЗаЧас', 'ТипЗаказа', 
            'ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа']]
    y_true = df['ТипТС']
    
    # Проверяем наличие пропущенных значений
    if X.isnull().any().any():
        logger.warning("\nПредупреждение: В данных есть пропущенные значения. Заполняем их.")
        X['Заказчик'] = X['Заказчик'].fillna('Новый заказчик')
        X['ТипЗаказа'] = X['ТипЗаказа'].fillna('Неизвестно')
        for col in ['ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа']:
            X[col] = X[col].fillna('Неизвестно')
        X['КоличествоПассажиров'] = X['КоличествоПассажиров'].fillna(X['КоличествоПассажиров'].median())
        X['ЦенаЗаЧас'] = X['ЦенаЗаЧас'].fillna(X['ЦенаЗаЧас'].median())
    
    # Создаем пул данных
    pool = Pool(X, cat_features=cat_features)
    
    # Делаем предсказания
    logger.info("\nВыполнение предсказаний...")
    y_pred = model.predict(pool)
    # Преобразуем предсказания в одномерный массив
    y_pred = y_pred.flatten()
    
    # Создаем график с результатами
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Результаты работы модели классификации типов ТС', fontsize=16, y=0.95)
    
    # 1. Матрица ошибок
    cm = confusion_matrix(y_true, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax1)
    ax1.set_title('Матрица ошибок')
    ax1.set_xlabel('Предсказанный тип ТС')
    ax1.set_ylabel('Истинный тип ТС')
    
    # 2. Точность по классам
    accuracies = []
    class_names = []
    for class_name in np.unique(y_true):
        class_mask = y_true == class_name
        accuracy = np.mean(y_pred[class_mask] == y_true[class_mask])
        accuracies.append(accuracy)
        class_names.append(class_name)
    
    sns.barplot(x=class_names, y=accuracies, ax=ax2)
    ax2.set_title('Точность предсказаний по типам ТС')
    ax2.set_xlabel('Тип ТС')
    ax2.set_ylabel('Точность')
    ax2.tick_params(axis='x', rotation=45)
    ax2.set_ylim(0, 1)
    
    # 3. Распределение предсказаний
    pred_counts = pd.Series(y_pred).value_counts().head(10)
    sns.barplot(x=pred_counts.index, y=pred_counts.values, ax=ax3)
    ax3.set_title('Топ-10 предсказанных типов ТС')
    ax3.set_xlabel('Тип ТС')
    ax3.set_ylabel('Количество предсказаний')
    ax3.tick_params(axis='x', rotation=45)
    
    # 4. Примеры предсказаний
    sample_size = min(5, len(df))
    sample_data = df.sample(sample_size)
    sample_pool = Pool(sample_data[['Заказчик', 'КоличествоПассажиров', 'ЦенаЗаЧас', 'ТипЗаказа', 
                                   'ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа']], 
                      cat_features=cat_features)
    sample_pred = model.predict(sample_pool)
    # Преобразуем предсказания для примеров в одномерный массив
    sample_pred = sample_pred.flatten()
    
    # Создаем таблицу с примерами
    cell_text = []
    for i in range(sample_size):
        row = [
            sample_data.iloc[i]['ТипТС'],
            sample_pred[i],
            sample_data.iloc[i]['ЦенаЗаЧас'],
            sample_data.iloc[i]['КоличествоПассажиров']
        ]
        cell_text.append(row)
    
    ax4.axis('off')
    table = ax4.table(
        cellText=cell_text,
        colLabels=['Истинный тип', 'Предсказанный тип', 'Цена за час', 'Кол-во пассажиров'],
        cellLoc='center',
        loc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    ax4.set_title('Примеры предсказаний')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, 'model_test_results.png'))
    plt.close(fig)
    return fig

# === МОДЕЛЬНЫЕ ГРАФИКИ ДЛЯ ДЕМОНСТРАЦИИ ===
def create_model_confusion_matrix(df, model, cat_features):
    X = df[['Заказчик', 'КоличествоПассажиров', 'ЦенаЗаЧас', 'ТипЗаказа',
            'ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа']]
    y_true = df['ТипТС']
    pool = Pool(X, cat_features=cat_features)
    y_pred = model.predict(pool).flatten()
    fig, ax = plt.subplots(figsize=(8, 6))
    cm = confusion_matrix(y_true, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax)
    ax.set_title('Матрица ошибок')
    ax.set_xlabel('Предсказанный тип ТС')
    ax.set_ylabel('Истинный тип ТС')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, 'model_confusion_matrix.png'))
    plt.close(fig)
    return fig

def create_model_accuracy_by_class(df, model, cat_features):
    X = df[['Заказчик', 'КоличествоПассажиров', 'ЦенаЗаЧас', 'ТипЗаказа',
            'ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа']]
    y_true = df['ТипТС']
    pool = Pool(X, cat_features=cat_features)
    y_pred = model.predict(pool).flatten()
    accuracies = []
    class_names = []
    for class_name in np.unique(y_true):
        class_mask = y_true == class_name
        accuracy = np.mean(y_pred[class_mask] == y_true[class_mask])
        accuracies.append(accuracy)
        class_names.append(class_name)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=class_names, y=accuracies, ax=ax)
    ax.set_title('Точность предсказаний по типам ТС')
    ax.set_xlabel('Тип ТС')
    ax.set_ylabel('Точность')
    ax.tick_params(axis='x', rotation=45)
    ax.set_ylim(0, 1)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, 'model_accuracy_by_class.png'))
    plt.close(fig)
    return fig

def create_model_pred_distribution(df, model, cat_features):
    X = df[['Заказчик', 'КоличествоПассажиров', 'ЦенаЗаЧас', 'ТипЗаказа',
            'ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа']]
    pool = Pool(X, cat_features=cat_features)
    y_pred = model.predict(pool).flatten()
    pred_counts = pd.Series(y_pred).value_counts().head(10)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=pred_counts.index, y=pred_counts.values, ax=ax)
    ax.set_title('Топ-10 предсказанных типов ТС')
    ax.set_xlabel('Тип ТС')
    ax.set_ylabel('Количество предсказаний')
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, 'model_pred_distribution.png'))
    plt.close(fig)
    return fig

def create_model_prediction_examples(df, model, cat_features):
    sample_size = min(5, len(df))
    sample_data = df.sample(sample_size)
    sample_pool = Pool(sample_data[['Заказчик', 'КоличествоПассажиров', 'ЦенаЗаЧас', 'ТипЗаказа',
                                   'ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа']],
                      cat_features=cat_features)
    sample_pred = model.predict(sample_pool).flatten()
    fig, ax = plt.subplots(figsize=(8, 3))
    cell_text = []
    for i in range(sample_size):
        row = [
            sample_data.iloc[i]['ТипТС'],
            sample_pred[i],
            sample_data.iloc[i]['ЦенаЗаЧас'],
            sample_data.iloc[i]['КоличествоПассажиров']
        ]
        cell_text.append(row)
    ax.axis('off')
    table = ax.table(
        cellText=cell_text,
        colLabels=['Истинный тип', 'Предсказанный тип', 'Цена за час', 'Кол-во пассажиров'],
        cellLoc='center',
        loc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    ax.set_title('Примеры предсказаний')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, 'model_prediction_examples.png'))
    plt.close(fig)
    return fig

def demonstrate_model_to_manager_window(df):
    """Окно с навигацией по графикам модели для руководителя"""
    logger.info("\n" + "="*50)
    logger.info("ДЕМОНСТРАЦИЯ РАБОТЫ МОДЕЛИ ДЛЯ РУКОВОДИТЕЛЯ")
    logger.info("="*50)
    
    # Загружаем профиль заказчиков
    customer_profile = load_customer_profile()
    if customer_profile is None:
        return None
    
    # Загружаем модель
    model_path = os.path.join(MODELS_DIR, "catboost_typets_model_v3.cbm")
    if not os.path.exists(model_path):
        logger.error(f"\nОШИБКА: Файл модели не найден по пути: {model_path}")
        logger.error("Проверьте, что:")
        logger.error("1. Файл модели находится в папке outputs/models/")
        logger.error("2. Имя файла точно соответствует: catboost_typets_model_v3.cbm")
        return None
    logger.info(f"\nЗагрузка модели из: {model_path}")
    model = CatBoostClassifier()
    model.load_model(model_path)
    
    # Объединяем данные с профилем заказчиков
    df = df.merge(customer_profile, on='Заказчик', how='left')
    cat_features = ['Заказчик', 'ТипЗаказа', 'ЛюбимыйТипТС', 'ИсторическийЛюбимыйТС', 'ЛюбимыйСтатусЗаказа']
    
    # Создаем окно
    model_window = tk.Toplevel()
    model_window.title("Демонстрация работы модели")
    model_window.geometry("1200x800")
    
    # Список функций-графиков для модели
    model_plots = [
        lambda: create_model_confusion_matrix(df, model, cat_features),
        lambda: create_model_accuracy_by_class(df, model, cat_features),
        lambda: create_model_pred_distribution(df, model, cat_features),
        lambda: create_model_prediction_examples(df, model, cat_features)
    ]
    
    # Менеджер графиков для окна модели
    PlotManager(model_window, df, None, custom_plots=model_plots)

def main():
    """Основная функция"""
    # Загружаем и подготавливаем данные
    df_orders, df_models, df_type_ts = load_and_prepare_data()
    
    # Выполняем анализы
    analyze_orders(df_orders, df_models)
    analyze_customers(df_orders)
    analyze_vehicles(df_orders, df_models, df_type_ts)
    
    # Тестируем модель
    test_model(df_orders)
    
    # Создаем главное окно
    root = tk.Tk()
    root.title("Анализ данных о заказах")
    root.geometry("1200x800")
    
    # Создаем менеджер графиков
    plot_manager = PlotManager(root, df_orders, df_models)
    
    # Демонстрируем работу модели в отдельном окне с навигацией
    demonstrate_model_to_manager_window(df_orders)
    
    # Запускаем главный цикл
    root.mainloop()
    
    logger.info("\nАнализ завершен!")

if __name__ == "__main__":
    main()
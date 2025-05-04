import os
import pandas as pd
from datetime import datetime

def save_web_order_data(data: dict):
    """
    Сохраняет данные, отправленные из веб-интерфейса, в Excel-файл.
    Если файл не существует — создаёт его.
    """
    filename = "orders_history.xlsx"
    fields = [
        "Дата", "Компания", "Название компании (если новая)",
        "Количество пассажиров", "Цена за час", "Тип заказа", "Рекомендации"
    ]

    record = {
        "Дата": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Компания": data.get("company"),
        "Название компании (если новая)": data.get("new_company_name"),
        "Количество пассажиров": data.get("passengers"),
        "Цена за час": data.get("price"),
        "Тип заказа": data.get("status"),
        "Рекомендации": "; ".join([f"{r['type']} ({r['probability']*100:.1f}%)" for r in data.get("recommendations", [])])
    }

    if os.path.exists(filename):
        df = pd.read_excel(filename)
    else:
        df = pd.DataFrame(columns=fields)

    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    df.to_excel(filename, index=False)

import os

# Устанавливаем переменные окружения ДО импорта app
os.environ["GOOGLE_CREDENTIALS_JSON"] = "./google.json"

# Абсолютный путь до папки docs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_PATH = os.path.join(BASE_DIR, "docs")

# Импортируем приложение
from app import app
from flask import send_from_directory

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

# Переопределяем путь к статическим файлам
app.static_folder = DOCS_PATH
app.static_url_path = ""

if __name__ == "__main__":
    print("Статика будет отдаваться из:", app.static_folder)
    app.run(debug=True)
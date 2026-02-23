# FAQ Bot

Этот бот предназначен для удобного общения с пользователями!  
Здесь используются технологии **PostgreSQL** и **Redis**.  
Бот написан на **aiogram**.

---

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourname/faq-bot.git
cd faq-bot
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте переменные окружения. Скопируйте .env.example в .env и измените данные:
```bash
DATABASE_URL=postgresql+psycopg2://postgres:pass@localhost:5432/postgres
BOT_TOKEN=YOUR_TOKEN
ASSETS_PATH=assets/faq
FAQ_PAGE_SIZE=4
COMPANY=EXAMPLE
```

5. Запуск
```bash
python main.py
```

Запустите бота и пользуйтесь им!

## Структура проекта
```
src/
├─ admin/       # Файлы для админской части
│  ├─ faq/      # Админская часть FAQ
│  └─ support/  # Админская часть поддержки
├─ assets/      # Файлы для FAQ
├─ crud/        # CRUD-функции
├─ database/    # PostgreSQL и Redis
├─ faq/         # Пользовательская часть FAQ
├─ model/       # Модели для БД
├─ root/        # Главное меню и "О нас"
├─ support/     # Пользовательская часть поддержки
├─ main.py      # Запуск проекта
└─ __init__.py  # Инициализация роутов
```
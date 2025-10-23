# Foodgram - Продуктовый помощник

![Workflow Status](https://github.com/eqsx000111/foodgram/actions/workflows/main.yml/badge.svg)

## Описание проекта

Foodgram - это веб-приложение для публикации и обмена кулинарными рецептами. Пользователи могут создавать собственные рецепты, добавлять чужие рецепты в избранное, подписываться на публикации других авторов и формировать список покупок на основе выбранных блюд.

### Основные возможности

- Публикация собственных рецептов с фотографиями
- Просмотр рецептов других пользователей
- Добавление рецептов в избранное
- Подписка на авторов
- Формирование списка покупок на основе выбранных рецептов
- Скачивание списка покупок в формате PDF
- Фильтрация рецептов по тегам и авторам
- Генерация коротких ссылок для удобного обмена рецептами
- Поиск ингредиентов по названию

## Стек технологий

**Backend:**
- Python 3.9+
- Django 4.2
- Django REST Framework 3.14
- PostgreSQL (при переменной окружения USE_SQLITE=True - есть возможность использования Sqlite3)
- Djoser (аутентификация)
- django-filter
- ReportLab (генерация PDF)

**DevOps:**
- Docker
- Docker Compose
- Nginx
- Gunicorn
- GitHub Actions (CI/CD)

## Установка и запуск проекта

### Требования

- Docker
- Docker Compose
- Git

### Клонирование репозитория

```bash
git clone git@github.com:eqsx000111/foodgram.git
cd foodgram
```

### Настройка переменных окружения

Создайте файл `.env` в корневой директории проекта на основе `.env.example`:

```bash
cp .env.example .env
```

Заполните файл `.env` следующими данными:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Database
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=your-strong-password
DB_HOST=db
DB_PORT=5432

```

### Запуск проекта

**Для разработки:**

```bash
# Создание и запуск контейнеров
docker-compose up -d --build

# Применение миграций
docker-compose exec backend python manage.py migrate

# Создание суперпользователя
docker-compose exec backend python manage.py createsuperuser

# Загрузка тестовых данных ингредиентов
docker-compose exec backend python manage.py load_ingredients --file data/ingredients.json

# Загрузка тестовых данных тегов
docker-compose exec backend python manage.py load_tags --file data/tags.json

# Сборка статики
docker-compose exec backend python manage.py collectstatic --no-input
```

**Для production:**

```bash
docker-compose -f docker-compose.production.yml up -d --build
```

Приложение будет доступно по адресу: [localhost](http://localhost/)

API документация: [API docs](http://localhost/api/docs/)

Административная панель: [Админка](http://localhost/admin/)


## Структура проекта

```
foodgram/
├── backend/
│   ├── api/                 # API приложение
│   │   ├── filters.py       # Фильтры для рецептов и ингредиентов
│   │   ├── permissions.py   # Права доступа
│   │   ├── serializers.py   # Сериализаторы
│   │   ├── services.py      # Бизнес-логика (генерация PDF)
│   │   ├── urls.py          # Маршруты API
│   │   └── views.py         # Представления
│   ├── recipes/             # Основное приложение
│   │   ├── models.py        # Модели данных
│   │   ├── admin.py         # Административная панель
│   │   └── management/      # Кастомные команды
│   ├── foodgram/            # Настройки проекта
│   ├── requirements.txt     # Зависимости Python
│   └── manage.py
├── frontend/                # Фронтенд приложение
├── foodgram_proxy/          # Конфигурация Nginx
├── docs/                    # Документация API
├── docker-compose.yml       # Docker Compose для разработки
├── docker-compose.production.yml  # Docker Compose для production
├── .env.example             # Пример файла с переменными окружения
└── README.md
```

## Административная панель

Доступ к административной панели: [http://localhost/admin/](http://localhost/admin/)

В панели администратора можно:
- Управлять пользователями
- Просматривать и редактировать рецепты
- Управлять тегами и ингредиентами
- Просматривать подписки и избранное

## CI/CD

Проект использует GitHub Actions для автоматизации развертывания. При пуше в ветку `main`:

1. Запускаются тесты
2. Собираются Docker образы
3. Образы загружаются на Docker Hub
4. Происходит автоматическое развертывание на сервере

Workflow находится в `.github/workflows/main.yml`

## Автор

**GitHub:** [eqsx000111](https://github.com/eqsx000111)
**Email:** [deddotu@yandex.ru](mailto:deddotu@yandex.ru)  
**ФИО:** Ильницкий Иван Александрович 
## Лицензия

Этот проект создан в образовательных целях.
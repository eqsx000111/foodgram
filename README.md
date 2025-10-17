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
- PostgreSQL
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

# Загрузка тестовых данных (опционально)
docker-compose exec backend python manage.py loaddata fixtures/ingredients.json
docker-compose exec backend python manage.py loaddata fixtures/tags.json

# Генерация коротких ссылок для существующих рецептов
docker-compose exec backend python manage.py generate_short_links

# Сборка статики
docker-compose exec backend python manage.py collectstatic --no-input
```

**Для production:**

```bash
docker-compose -f docker-compose.production.yml up -d --build
```

Приложение будет доступно по адресу: `http://localhost/`

API документация: `http://localhost/api/docs/`

Административная панель: `http://localhost/admin/`

## API Endpoints

### Аутентификация

```
POST /api/auth/token/login/  - Получение токена
POST /api/auth/token/logout/ - Удаление токена
```

### Пользователи

```
GET    /api/users/                - Список пользователей
POST   /api/users/                - Регистрация пользователя
GET    /api/users/{id}/           - Профиль пользователя
GET    /api/users/me/             - Текущий пользователь
POST   /api/users/set_password/   - Изменение пароля
PUT    /api/users/me/avatar/      - Загрузка аватара
DELETE /api/users/me/avatar/      - Удаление аватара
```

### Подписки

```
GET    /api/users/subscriptions/     - Мои подписки
POST   /api/users/{id}/subscribe/    - Подписаться на пользователя
DELETE /api/users/{id}/subscribe/    - Отписаться от пользователя
```

### Рецепты

```
GET    /api/recipes/                      - Список рецептов
POST   /api/recipes/                      - Создание рецепта
GET    /api/recipes/{id}/                 - Получение рецепта
PATCH  /api/recipes/{id}/                 - Обновление рецепта
DELETE /api/recipes/{id}/                 - Удаление рецепта
GET    /api/recipes/{id}/get-link/        - Получить короткую ссылку
POST   /api/recipes/{id}/favorite/        - Добавить в избранное
DELETE /api/recipes/{id}/favorite/        - Удалить из избранного
POST   /api/recipes/{id}/shopping_cart/   - Добавить в список покупок
DELETE /api/recipes/{id}/shopping_cart/   - Удалить из списка покупок
GET    /api/recipes/download_shopping_cart/ - Скачать список покупок (PDF)
```

### Фильтрация рецептов

```
GET /api/recipes/?is_favorited=1           - Рецепты в избранном
GET /api/recipes/?is_in_shopping_cart=1    - Рецепты в списке покупок
GET /api/recipes/?author=1                 - Рецепты автора
GET /api/recipes/?tags=breakfast,lunch     - Рецепты с тегами
```

### Ингредиенты и теги

```
GET /api/ingredients/           - Список ингредиентов
GET /api/ingredients/{id}/      - Конкретный ингредиент
GET /api/ingredients/?name=мука - Поиск по названию
GET /api/tags/                  - Список тегов
GET /api/tags/{id}/             - Конкретный тег
```

### Короткие ссылки

```
GET /s/{short_link}/  - Редирект на полный URL рецепта
```

## Примеры запросов

### Регистрация пользователя

```bash
curl -X POST http://localhost/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "username",
    "first_name": "Имя",
    "last_name": "Фамилия",
    "password": "StrongPassword123"
  }'
```

### Получение токена

```bash
curl -X POST http://localhost/api/auth/token/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "StrongPassword123"
  }'
```

### Создание рецепта

```bash
curl -X POST http://localhost/api/recipes/ \
  -H "Authorization: Token your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Название рецепта",
    "text": "Описание приготовления",
    "cooking_time": 30,
    "image": "data:image/png;base64,iVBORw0KGgo...",
    "tags": [1, 2],
    "ingredients": [
      {"id": 1, "amount": 200},
      {"id": 2, "amount": 100}
    ]
  }'
```

### Получение списка рецептов в избранном

```bash
curl -X GET "http://localhost/api/recipes/?is_favorited=1" \
  -H "Authorization: Token your-token-here"
```

### Получение короткой ссылки

```bash
curl -X GET http://localhost/api/recipes/1/get-link/ \
  -H "Authorization: Token your-token-here"
```

Ответ:
```json
{
  "short-link": "http://localhost/s/aBc123"
}
```

### Скачивание списка покупок

```bash
curl -X GET http://localhost/api/recipes/download_shopping_cart/ \
  -H "Authorization: Token your-token-here" \
  --output shopping_list.pdf
```

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

Доступ к административной панели: `http://localhost/admin/`

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

## Лицензия

Этот проект создан в образовательных целях.
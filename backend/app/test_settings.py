"""
Настройки Django для фаззинг-тестов и других локальных тестов.
Использует SQLite in-memory вместо PostgreSQL, чтобы тесты можно было
запускать без запущенного контейнера с БД.
"""

from app.settings import *  # noqa: F401, F403

# Переопределяем БД на SQLite in-memory
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Отключаем лишние проверки для тестов
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',  # быстрее BCrypt в тестах
]

# Centrifugo — заглушки (реальный сервер не нужен для тестов)
CENTRIFUGO_HTTP_API_ENDPOINT = 'http://localhost:8001'
CENTRIFUGO_HTTP_API_KEY = 'test-api-key'
CENTRIFUGO_TOKEN_SECRET = 'test-token-secret'

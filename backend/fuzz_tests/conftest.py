"""
Конфигурация pytest для фаззинг-тестов.

Pytest-django автоматически подхватывает DJANGO_SETTINGS_MODULE из pytest.ini
(app.test_settings), который использует SQLite :memory: вместо PostgreSQL.
Дополнительная настройка здесь не нужна — этот файл зарезервирован для
фикстур, специфичных для директории fuzz_tests/.
"""

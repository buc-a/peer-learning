"""
Фаззинг-тесты для Post API.

Используется библиотека Hypothesis для генерации случайных данных и проверки
устойчивости API к неожиданным входным данным.

Покрываемые сценарии:
- Создание поста с произвольными строками (title, description, skill)
- Фильтрация постов по произвольным строкам (?skill=..., ?author=...)
- Обновление поста (PUT/PATCH) с произвольными данными
- Проверка корректности валидации сериализатора с граничными значениями
"""

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st
from django.contrib.auth.models import User
from django.test import RequestFactory
from rest_framework.test import APIClient
from rest_framework import status

from post.models import Post
from post.serializers import PostWriteSerializer, PostSerializer


# ──────────────────────────────────────────────
# Стратегии генерации данных
# ──────────────────────────────────────────────

# Произвольные строки до 200 символов (юникод, эмодзи, спец. символы)
any_text = st.text(min_size=0, max_size=200)

# Строки, не превышающие максимальную длину поля title (200 символов)
valid_title = st.text(min_size=1, max_size=200)

# Строки для поля skill (до 100 символов)
valid_skill = st.text(min_size=1, max_size=100)

# Строки для description (произвольной длины)
valid_description = st.text(min_size=0, max_size=5000)

# Потенциально опасные строки (SQL-инъекции, XSS, спец. символы)
dangerous_strings = st.one_of(
    st.just("' OR '1'='1"),
    st.just("'; DROP TABLE post_post; --"),
    st.just("<script>alert('xss')</script>"),
    st.just("../../../etc/passwd"),
    st.just("\x00\x01\x02\x03"),
    st.just("A" * 201),          # превышает max_length title
    st.just("B" * 101),          # превышает max_length skill
    st.just(""),                  # пустая строка
    st.just("   "),               # только пробелы
    st.just("null"),
    st.just("None"),
    st.just("undefined"),
    st.just("NaN"),
    st.just("0"),
    st.just("-1"),
    st.just("9" * 50),
    st.just("日本語テスト"),       # мультибайт символы
    st.just("مرحبا بالعالم"),    # арабский язык (RTL)
    st.just("𝔽𝕦𝕫𝕫𝕚𝕟𝕘"),       # unicode supplementary
)


# ──────────────────────────────────────────────
# Тесты для PostWriteSerializer
# ──────────────────────────────────────────────

@pytest.mark.django_db
class TestPostSerializerFuzzing:
    """Фаззинг валидации PostWriteSerializer."""

    @given(
        title=valid_title,
        description=valid_description,
        skill=valid_skill,
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_valid_data_always_validates_or_rejects_gracefully(self, title, description, skill):
        """
        При любых корректных строках сериализатор должен либо успешно
        валидировать данные, либо вернуть ошибку валидации — но НИКОГДА
        не выбрасывать необработанное исключение.
        """
        data = {'title': title, 'description': description, 'skill': skill}
        serializer = PostWriteSerializer(data=data)
        # is_valid() должен возвращать bool без исключений
        result = serializer.is_valid()
        assert isinstance(result, bool)
        # Если невалидно — должны быть ошибки
        if not result:
            assert serializer.errors

    @given(
        title=dangerous_strings,
        description=dangerous_strings,
        skill=dangerous_strings,
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_dangerous_strings_dont_crash_serializer(self, title, description, skill):
        """
        Потенциально опасные строки (SQL-инъекции, XSS, спец-символы)
        не должны приводить к необработанному исключению в сериализаторе.
        """
        data = {'title': title, 'description': description, 'skill': skill}
        serializer = PostWriteSerializer(data=data)
        try:
            serializer.is_valid()
        except Exception as exc:
            pytest.fail(
                f"Сериализатор выбросил неожиданное исключение: {exc}\n"
                f"Входные данные: {data}"
            )

    @given(
        title=st.text(min_size=201, max_size=1000),  # превышение max_length
    )
    @settings(max_examples=20)
    def test_title_too_long_fails_validation(self, title):
        """
        title длиннее 200 символов должен НЕ проходить валидацию.
        """
        data = {'title': title, 'description': 'desc', 'skill': 'python'}
        serializer = PostWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert 'title' in serializer.errors

    @given(
        skill=st.text(min_size=101, max_size=500),  # превышение max_length
    )
    @settings(max_examples=20)
    def test_skill_too_long_fails_validation(self, skill):
        """
        skill длиннее 100 символов должен НЕ проходить валидацию.
        """
        data = {'title': 'Нормальный заголовок', 'description': 'desc', 'skill': skill}
        serializer = PostWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert 'skill' in serializer.errors


# ──────────────────────────────────────────────
# Тесты для API-эндпоинтов через APIClient
# ──────────────────────────────────────────────

@pytest.mark.django_db
class TestPostAPIFuzzing:
    """Фаззинг HTTP-эндпоинтов Post API."""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='fuzz_user', password='fuzz_pass123'
        )
        self.client.force_authenticate(user=self.user)

    @given(
        title=valid_title,
        description=valid_description,
        skill=valid_skill,
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_create_post_always_returns_http_response(self, title, description, skill):
        """
        POST /api/posts/ с произвольными данными должен всегда возвращать
        HTTP-ответ (200, 201, 400, 403 и т.д.), но не падать с 500.
        """
        response = self.client.post(
            '/api/posts/',
            data={'title': title, 'description': description, 'skill': skill},
            format='json'
        )
        assert response.status_code != 500, (
            f"Получен HTTP 500 при данных: title={title!r}, skill={skill!r}"
        )
        assert response.status_code in (
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    @given(skill_filter=any_text)
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_list_posts_with_arbitrary_skill_filter(self, skill_filter):
        """
        GET /api/posts/?skill=<fuzz> не должен возвращать HTTP 500.
        Фильтрация по произвольным строкам должна быть безопасной.
        """
        response = self.client.get('/api/posts/', {'skill': skill_filter})
        assert response.status_code != 500, (
            f"Получен HTTP 500 при ?skill={skill_filter!r}"
        )

    @given(author_filter=any_text)
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_list_posts_with_arbitrary_author_filter(self, author_filter):
        """
        GET /api/posts/?author=<fuzz> не должен возвращать HTTP 500.
        При некорректном author ID должен возвращаться 400 или пустой список.
        """
        response = self.client.get('/api/posts/', {'author': author_filter})
        assert response.status_code != 500, (
            f"Получен HTTP 500 при ?author={author_filter!r}"
        )

    @given(post_id=st.integers(min_value=-10**9, max_value=10**9))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_get_nonexistent_post_returns_404(self, post_id):
        """
        GET /api/posts/<id>/ с произвольным числовым ID не должен падать с 500.
        Несуществующие записи должны возвращать 404.
        """
        response = self.client.get(f'/api/posts/{post_id}/')
        assert response.status_code in (
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
        ), f"Неожиданный статус {response.status_code} для ID={post_id}"

    @given(
        new_title=valid_title,
        new_skill=valid_skill,
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_patch_own_post_with_arbitrary_data(self, new_title, new_skill):
        """
        PATCH /api/posts/<id>/ с произвольными полями не должен возвращать 500.
        """
        post = Post.objects.create(
            author=self.user,
            title='Исходный заголовок',
            description='Описание',
            skill='python'
        )
        response = self.client.patch(
            f'/api/posts/{post.id}/',
            data={'title': new_title, 'skill': new_skill},
            format='json'
        )
        assert response.status_code != 500, (
            f"HTTP 500 при PATCH: title={new_title!r}, skill={new_skill!r}"
        )
        post.delete()

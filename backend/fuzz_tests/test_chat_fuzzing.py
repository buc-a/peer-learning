"""
Фаззинг-тесты для Chat API.

Покрываемые сценарии:
- Отправка сообщений с произвольным контентом (unicode, спец. символы, XSS)
- StartChat с произвольными user_id (негативные числа, строки, None)
- Поиск пользователей по произвольным строкам (?q=...)
- Проверка граничных значений контента сообщений
"""

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from chat.models import Room, RoomMember, Message


# ──────────────────────────────────────────────
# Стратегии генерации данных
# ──────────────────────────────────────────────

any_text = st.text(min_size=0, max_size=500)
nonempty_text = st.text(min_size=1, max_size=500)

# Произвольные «user_id» — числа, строки, None
arbitrary_user_id = st.one_of(
    st.integers(min_value=-10**9, max_value=10**9),
    st.just(None),
    st.just(""),
    st.just("abc"),
    st.just("0"),
    st.just("-1"),
    st.just("9" * 20),
    st.just(True),
    st.just(False),
)

# Потенциально опасный контент сообщений
dangerous_content = st.one_of(
    st.just("<script>alert(1)</script>"),
    st.just("' OR 1=1 --"),
    st.just("\n\r\t"),
    st.just("\x00"),
    st.just("🔥" * 100),
    st.just("A" * 10000),         # очень длинное сообщение
    st.just(""),
    st.just("   "),
    st.just("null"),
    st.just("{{7*7}}"),            # template injection
    st.just("%s %s %s %s %s"),    # format string
    st.just("../../../../etc/passwd"),
)


# ──────────────────────────────────────────────
# Тесты StartChat API
# ──────────────────────────────────────────────

@pytest.mark.django_db
class TestStartChatFuzzing:
    """Фаззинг эндпоинта POST /api/chat/start/."""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='fuzz_chat_user', password='pass123'
        )
        self.client.force_authenticate(user=self.user)

    @given(user_id=arbitrary_user_id)
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_start_chat_arbitrary_user_id_no_500(self, user_id):
        """
        POST /api/chat/start/ с произвольным user_id не должен возвращать HTTP 500.
        Ожидаемые ответы: 200, 201, 400, 404.
        """
        response = self.client.post(
            '/api/chat/start/',
            data={'user_id': user_id},
            format='json'
        )
        assert response.status_code != 500, (
            f"Получен HTTP 500 при user_id={user_id!r}"
        )
        assert response.status_code in (
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
        )

    def test_start_chat_with_self_returns_400(self):
        """
        Попытка начать чат с самим собой должна возвращать HTTP 400.
        """
        response = self.client.post(
            '/api/chat/start/',
            data={'user_id': self.user.pk},
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_start_chat_missing_user_id_returns_400(self):
        """
        POST /api/chat/start/ без поля user_id должен возвращать HTTP 400.
        """
        response = self.client.post('/api/chat/start/', data={}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @given(extra_field=any_text, extra_value=any_text)
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_start_chat_with_extra_fields_no_500(self, extra_field, extra_value):
        """
        POST /api/chat/start/ с лишними полями не должен падать с 500.
        """
        response = self.client.post(
            '/api/chat/start/',
            data={'user_id': self.user.pk, extra_field: extra_value},
            format='json'
        )
        assert response.status_code != 500


# ──────────────────────────────────────────────
# Тесты Message API
# ──────────────────────────────────────────────

@pytest.mark.django_db
class TestMessageFuzzing:
    """Фаззинг эндпоинта POST /api/chat/rooms/<id>/messages/."""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='fuzz_msg_user', password='pass123'
        )
        self.other_user = User.objects.create_user(
            username='fuzz_msg_other', password='pass123'
        )
        self.client.force_authenticate(user=self.user)

        # Создаём комнату и добавляем участников
        self.room = Room.objects.create(name='fuzz_room')
        RoomMember.objects.create(room=self.room, user=self.user)
        RoomMember.objects.create(room=self.room, user=self.other_user)

    @given(content=nonempty_text)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_send_message_arbitrary_content_no_500(self, content):
        """
        POST /api/chat/rooms/<id>/messages/ с произвольным контентом не должен
        возвращать HTTP 500.
        """
        response = self.client.post(
            f'/api/chat/rooms/{self.room.pk}/messages/',
            data={'content': content},
            format='json'
        )
        assert response.status_code != 500, (
            f"HTTP 500 при content={content[:50]!r}..."
        )
        assert response.status_code in (
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
        )

    @given(content=dangerous_content)
    @settings(max_examples=15, suppress_health_check=[HealthCheck.too_slow])
    def test_send_dangerous_content_no_500(self, content):
        """
        Отправка потенциально опасных строк (XSS, SQL-инъекции, спец. символы)
        не должна приводить к HTTP 500.
        """
        response = self.client.post(
            f'/api/chat/rooms/{self.room.pk}/messages/',
            data={'content': content},
            format='json'
        )
        assert response.status_code != 500, (
            f"HTTP 500 при опасном content={content!r}"
        )

    @given(room_id=st.integers(min_value=1, max_value=10**9))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_get_messages_nonexistent_room_no_500(self, room_id):
        """
        GET /api/chat/rooms/<fuzz_id>/messages/ для несуществующей комнаты
        должен возвращать 403 или 404, но не 500.
        """
        response = self.client.get(f'/api/chat/rooms/{room_id}/messages/')
        assert response.status_code != 500, (
            f"HTTP 500 при room_id={room_id}"
        )
        assert response.status_code in (
            status.HTTP_200_OK,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )


# ──────────────────────────────────────────────
# Тесты User Search API
# ──────────────────────────────────────────────

@pytest.mark.django_db
class TestUserSearchFuzzing:
    """Фаззинг эндпоинта GET /api/chat/users/ (поиск пользователей)."""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='fuzz_search_user', password='pass123'
        )
        self.client.force_authenticate(user=self.user)

    @given(query=any_text)
    @settings(max_examples=40, suppress_health_check=[HealthCheck.too_slow])
    def test_user_search_arbitrary_query_no_500(self, query):
        """
        GET /api/chat/users/?q=<fuzz> с произвольными строками не должен
        возвращать HTTP 500. Поиск по произвольному запросу должен быть безопасным.
        """
        response = self.client.get('/api/chat/users/', {'q': query})
        assert response.status_code != 500, (
            f"HTTP 500 при ?q={query!r}"
        )
        assert response.status_code == status.HTTP_200_OK

    @given(
        query=st.one_of(
            st.just("' OR '1'='1"),
            st.just("admin' --"),
            st.just("%; DROP TABLE auth_user; --"),
            st.just("%"),
            st.just("_"),
            st.just("\\"),
            st.just("\x00"),
        )
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_user_search_sql_injection_attempts_no_500(self, query):
        """
        SQL-инъекции в параметре поиска не должны приводить к 500.
        Django ORM должен безопасно экранировать параметры запроса.
        """
        response = self.client.get('/api/chat/users/', {'q': query})
        assert response.status_code != 500, (
            f"HTTP 500 при SQL-инъекции: ?q={query!r}"
        )

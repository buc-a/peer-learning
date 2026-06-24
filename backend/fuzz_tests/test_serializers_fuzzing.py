"""
Фаззинг-тесты для сериализаторов.

Покрываемые сценарии:
- Подача произвольных типов данных вместо ожидаемых (int вместо str, dict, list и т.д.)
- Проверка отсутствия обязательных полей
- Проверка граничных значений числовых полей
- Проверка поведения при полностью случайных JSON-структурах
"""

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase

from post.serializers import PostWriteSerializer
from chat.serializers import MessageSerializer


# ──────────────────────────────────────────────
# Стратегии генерации произвольных JSON-значений
# ──────────────────────────────────────────────

# Примитивные JSON-значения
json_primitives = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(max_size=300),
)

# Произвольные JSON-совместимые значения (рекурсивно)
json_values = st.recursive(
    json_primitives,
    lambda children: st.one_of(
        st.lists(children, max_size=5),
        st.dictionaries(st.text(max_size=20), children, max_size=5),
    ),
    max_leaves=10,
)

# Произвольные словари (имитируют request.data)
arbitrary_dict = st.dictionaries(
    keys=st.text(min_size=0, max_size=50),
    values=json_values,
    max_size=10,
)


# ──────────────────────────────────────────────
# Фаззинг PostWriteSerializer
# ──────────────────────────────────────────────

@pytest.mark.django_db
class TestPostWriteSerializerFuzzing:
    """Фаззинг PostWriteSerializer с произвольными типами данных."""

    @given(data=arbitrary_dict)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_arbitrary_dict_never_raises(self, data):
        """
        Произвольный словарь как входные данные не должен приводить к
        необработанному исключению — только к ValidationError или False.
        """
        serializer = PostWriteSerializer(data=data)
        try:
            serializer.is_valid()
        except Exception as exc:
            pytest.fail(
                f"PostWriteSerializer.is_valid() выбросил исключение: {type(exc).__name__}: {exc}\n"
                f"Данные: {data}"
            )

    @given(
        title=json_values,
        description=json_values,
        skill=json_values,
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_wrong_types_in_fields_never_raises(self, title, description, skill):
        """
        Подача неправильных типов (int, list, dict, None) в строковые поля
        не должна вызывать необработанное исключение.
        """
        data = {'title': title, 'description': description, 'skill': skill}
        serializer = PostWriteSerializer(data=data)
        try:
            serializer.is_valid()
        except Exception as exc:
            pytest.fail(
                f"Исключение при неправильных типах: {type(exc).__name__}: {exc}\n"
                f"Данные: {data}"
            )

    @given(missing_field=st.sampled_from(['title', 'description', 'skill']))
    @settings(max_examples=10)
    def test_missing_required_field_fails_validation(self, missing_field):
        """
        Отсутствие любого из обязательных полей должно делать данные невалидными.
        """
        data = {'title': 'Заголовок', 'description': 'Описание', 'skill': 'python'}
        del data[missing_field]
        serializer = PostWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert missing_field in serializer.errors

    def test_empty_dict_fails_validation(self):
        """Пустой словарь должен проваливать валидацию."""
        serializer = PostWriteSerializer(data={})
        assert not serializer.is_valid()
        assert len(serializer.errors) > 0

    def test_null_values_fail_validation(self):
        """None-значения в обязательных полях должны проваливать валидацию."""
        data = {'title': None, 'description': None, 'skill': None}
        serializer = PostWriteSerializer(data=data)
        assert not serializer.is_valid()


# ──────────────────────────────────────────────
# Фаззинг MessageSerializer
# ──────────────────────────────────────────────

@pytest.mark.django_db
class TestMessageSerializerFuzzing:
    """Фаззинг MessageSerializer."""

    @given(data=arbitrary_dict)
    @settings(max_examples=80, suppress_health_check=[HealthCheck.too_slow])
    def test_arbitrary_dict_never_raises(self, data):
        """
        Произвольный словарь не должен вызывать необработанное исключение
        при вызове is_valid() у MessageSerializer.
        """
        serializer = MessageSerializer(data=data)
        try:
            serializer.is_valid()
        except Exception as exc:
            pytest.fail(
                f"MessageSerializer.is_valid() выбросил исключение: {type(exc).__name__}: {exc}\n"
                f"Данные: {data}"
            )

    @given(content=json_values)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_wrong_content_type_never_raises(self, content):
        """
        Произвольный тип значения в поле content не должен вызывать
        необработанное исключение.
        """
        serializer = MessageSerializer(data={'content': content})
        try:
            serializer.is_valid()
        except Exception as exc:
            pytest.fail(
                f"Исключение при content={content!r}: {type(exc).__name__}: {exc}"
            )

    def test_empty_content_fails_validation(self):
        """Пустая строка в content должна проваливать валидацию."""
        serializer = MessageSerializer(data={'content': ''})
        assert not serializer.is_valid()

    def test_missing_content_fails_validation(self):
        """Отсутствие поля content должно проваливать валидацию."""
        serializer = MessageSerializer(data={})
        assert not serializer.is_valid()
        assert 'content' in serializer.errors


# ──────────────────────────────────────────────
# Граничные значения: строки максимальной/минимальной длины
# ──────────────────────────────────────────────

@pytest.mark.django_db
class TestBoundaryValuesFuzzing:
    """Тестирование граничных значений для полей моделей."""

    @given(length=st.integers(min_value=1, max_value=200))
    @settings(max_examples=20)
    def test_title_at_boundary_validates(self, length):
        """
        title длиной от 1 до 200 символов должен проходить валидацию.
        """
        title = "X" * length
        serializer = PostWriteSerializer(
            data={'title': title, 'description': 'ok', 'skill': 'python'}
        )
        assert serializer.is_valid(), (
            f"title длиной {length} не прошёл валидацию: {serializer.errors}"
        )

    @given(length=st.integers(min_value=201, max_value=2000))
    @settings(max_examples=20)
    def test_title_over_200_fails(self, length):
        """title длиннее 200 символов должен проваливать валидацию."""
        title = "X" * length
        serializer = PostWriteSerializer(
            data={'title': title, 'description': 'ok', 'skill': 'python'}
        )
        assert not serializer.is_valid()
        assert 'title' in serializer.errors

    @given(length=st.integers(min_value=1, max_value=100))
    @settings(max_examples=20)
    def test_skill_at_boundary_validates(self, length):
        """skill длиной от 1 до 100 символов должен проходить валидацию."""
        skill = "Y" * length
        serializer = PostWriteSerializer(
            data={'title': 'Заголовок', 'description': 'ok', 'skill': skill}
        )
        assert serializer.is_valid(), (
            f"skill длиной {length} не прошёл валидацию: {serializer.errors}"
        )

    @given(length=st.integers(min_value=101, max_value=1000))
    @settings(max_examples=20)
    def test_skill_over_100_fails(self, length):
        """skill длиннее 100 символов должен проваливать валидацию."""
        skill = "Y" * length
        serializer = PostWriteSerializer(
            data={'title': 'Заголовок', 'description': 'ok', 'skill': skill}
        )
        assert not serializer.is_valid()
        assert 'skill' in serializer.errors

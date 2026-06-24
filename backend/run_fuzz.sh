#!/usr/bin/env bash
# =============================================================================
# run_fuzz.sh — запуск фаззинг-тестов проекта peer-learning
# =============================================================================
# Использование:
#   chmod +x backend/run_fuzz.sh
#   ./backend/run_fuzz.sh                  # все фаззинг-тесты
#   ./backend/run_fuzz.sh post             # только тесты Post API
#   ./backend/run_fuzz.sh chat             # только тесты Chat API
#   ./backend/run_fuzz.sh serializers      # только тесты сериализаторов
#   ./backend/run_fuzz.sh --verbose        # подробный вывод
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Цвета вывода ──────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=============================================${NC}"
echo -e "${CYAN}   Фаззинг-тестирование peer-learning        ${NC}"
echo -e "${CYAN}=============================================${NC}"

# ── Проверка наличия Python и pip ─────────────────────────────────────────────
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ОШИБКА] Python не найден. Установите Python 3.10+${NC}"
    exit 1
fi

PYTHON=$(command -v python3 || command -v python)
echo -e "${BLUE}[INFO] Используется Python: $($PYTHON --version)${NC}"

# ── Установка зависимостей ────────────────────────────────────────────────────
echo -e "\n${YELLOW}[STEP 1] Установка зависимостей...${NC}"
$PYTHON -m pip install -q hypothesis pytest pytest-django djangorestframework
echo -e "${GREEN}[OK] Зависимости установлены${NC}"

# ── Настройка Django ──────────────────────────────────────────────────────────
# Используем test_settings.py — SQLite :memory:, без PostgreSQL
export DJANGO_SETTINGS_MODULE=app.test_settings
echo -e "${BLUE}[INFO] DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} (SQLite in-memory)${NC}"

# ── Выбор тестов по аргументу ─────────────────────────────────────────────────
VERBOSE=""
TARGET="fuzz_tests/"

for arg in "$@"; do
    case $arg in
        post)       TARGET="fuzz_tests/test_post_fuzzing.py" ;;
        chat)       TARGET="fuzz_tests/test_chat_fuzzing.py" ;;
        serializers) TARGET="fuzz_tests/test_serializers_fuzzing.py" ;;
        --verbose|-v) VERBOSE="-v" ;;
        --help|-h)
            echo "Использование: $0 [post|chat|serializers] [--verbose]"
            exit 0
            ;;
    esac
done

# ── Запуск тестов ─────────────────────────────────────────────────────────────
echo -e "\n${YELLOW}[STEP 2] Запуск фаззинг-тестов: ${TARGET}${NC}"
echo -e "${BLUE}[INFO] Конфигурация pytest: pytest.ini / pyproject.toml${NC}\n"

$PYTHON -m pytest \
    $TARGET \
    $VERBOSE \
    --tb=short \
    --no-header \
    -p no:warnings \
    --hypothesis-seed=0 \
    -x \
    2>&1

EXIT_CODE=$?

echo -e "\n${CYAN}=============================================${NC}"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}[РЕЗУЛЬТАТ] Все фаззинг-тесты прошли успешно ✓${NC}"
else
    echo -e "${RED}[РЕЗУЛЬТАТ] Тесты завершились с ошибками (код: $EXIT_CODE)${NC}"
fi
echo -e "${CYAN}=============================================${NC}"

# Очистка тестовой БД SQLite (если создавалась)
if [ -f "test_fuzz.db" ]; then
    rm -f test_fuzz.db
fi

exit $EXIT_CODE

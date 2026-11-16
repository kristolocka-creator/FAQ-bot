from pathlib import Path
import pytest
from support_bot import SupportBot
import csv

FAQ_PATH = Path(__file__).parent / "data" / "faq.json"


@pytest.fixture
def bot():
    return SupportBot(str(FAQ_PATH))


def test_load_faq(bot):
    """Проверяет загрузку базы FAQ."""

    assert len(bot.faq) >= 5


def test_missing_file():
    """Проверяет обработку отсутствующего файла."""

    with pytest.raises(FileNotFoundError):
        SupportBot("data/missing.json")


def test_exact_match(bot):
    """Проверяет поиск по точному ключевому слову."""

    answer = bot.get_answer("Как сменить пароль?")
    assert "Сменить пароль" in answer


def test_synonym_match(bot):
    """Проверяет поиск по синониму («поменять» → «сменить»)."""

    answer = bot.get_answer("Как поменять пароль?")
    assert "Сменить пароль" in answer


def test_partial_match(bot):
    """Проверяет поиск по части ключевых слов."""

    answer = bot.get_answer("Подскажите про пароль")
    assert "Сменить пароль" in answer


def test_no_match(bot):
    """Проверяет ответ на неизвестный вопрос."""

    answer = bot.get_answer("Как приготовить борщ?")
    assert answer == "Извините, я не понял вопрос. Пожалуйста, уточните."


def test_history_filled(bot):
    """Проверяет, что история заполняется после ответа."""

    bot.get_answer("Как сменить пароль?")
    assert len(bot.history) == 1
    assert bot.history[0]["user_question"] == "Как сменить пароль?"


def test_help_command(bot):
    """Проверяет команду /help."""

    answer = bot.get_answer("/help")
    assert "/history" in answer
    assert "/export" in answer


def test_export_command(bot, tmp_path, monkeypatch):
    """Проверяет /export и создание CSV."""

    # Перенаправляем рабочий каталог во временную папку
    monkeypatch.chdir(tmp_path)

    bot.get_answer("Как сменить пароль?")
    result = bot.get_answer("/export")

    assert "История экспортирована" in result
    assert (tmp_path / "history.csv").exists()


def test_history_shows_only_last_five(bot):
    """Проверяет, что /history показывает только последние 5 вопросов."""
    bot.get_answer("код доступа")

    for question in [
        "поддержка",
        "помощь",
        "оператор",
        "связаться",
        "Как связаться с поддержкой?",
    ]:
        bot.get_answer(question)

    result = bot.get_answer("/history")

    assert "код доступа" not in result
    assert result.count("Q:") == 5


def test_unknown_question_is_logged(bot, tmp_path, monkeypatch):
    """Проверяет запись неизвестного вопроса в лог."""
    monkeypatch.chdir(tmp_path)

    bot.get_answer("Как приготовить борщ?")

    log_path = tmp_path / "data" / "unknown_questions.log"

    assert log_path.exists()
    assert "Как приготовить борщ?" in log_path.read_text(encoding="utf-8")


def test_export_history_csv_content(bot, tmp_path):
    """Проверяет заголовки и содержимое CSV-файла."""
    bot.get_answer("Как сменить пароль?")

    csv_path = tmp_path / "history.csv"
    bot.export_history(csv_path)

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    assert reader.fieldnames == [
        "timestamp",
        "user_question",
        "bot_answer",
    ]

    assert len(rows) == 1
    assert rows[0]["user_question"] == "Как сменить пароль?"
    assert "Сменить пароль" in rows[0]["bot_answer"]
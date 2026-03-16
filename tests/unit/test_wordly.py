from unittest.mock import AsyncMock, patch

import pytest

from functions import wordly


@pytest.mark.asyncio
async def test_load_words_from_db_filters_length_and_lowercase(monkeypatch):
    async_mock = AsyncMock()
    async_mock.__aenter__.return_value.execute_all.return_value = [
        {"word": "Домик"},
        {"word": " КНИГА "},
        {"word": "too_long"},
        {"word": None},
    ]

    with patch("functions.wordly.Database", return_value=async_mock):
        words = await wordly._load_words()

    # Только слова длиной 5, в нижнем регистре
    assert set(words) == {"домик", "книга"}


@pytest.mark.asyncio
async def test_load_words_from_file_when_db_fails(tmp_path, monkeypatch):
    # Смоделировать падение БД
    async_mock = AsyncMock()
    async_mock.__aenter__.side_effect = Exception("db error")

    with patch("functions.wordly.Database", return_value=async_mock):
        # Подменяем путь к static/wordly_words_ru.txt на временный
        base_dir = tmp_path
        static_dir = base_dir / "static"
        static_dir.mkdir()
        words_file = static_dir / "wordly_words_ru.txt"
        words_file.write_text("Домик\nкнига\nкорот\nслишкомдлина\n", encoding="utf-8")

        with patch("functions.wordly.Path") as path_cls:
            # Path(__file__).resolve().parent.parent → base_dir
            path_instance = path_cls.return_value
            path_instance.resolve.return_value.parent.parent = base_dir

            words = await wordly._load_words()

    # Из файла берутся только 5-буквенные слова
    assert set(words) == {"домик", "книга", "корот"}


@pytest.mark.asyncio
async def test_load_words_fallback_used_when_db_and_file_empty(monkeypatch):
    async_mock = AsyncMock()
    async_mock.__aenter__.return_value.execute_all.return_value = []

    with patch("functions.wordly.Database", return_value=async_mock), patch(
        "functions.wordly.Path.read_text", side_effect=OSError("no file")
    ):
        words = await wordly._load_words()

    # Фолбэк из кода содержит только 5-буквенные слова после фильтрации
    assert all(len(w) == 5 for w in words)
    # хотя бы несколько ожидаемых слов присутствуют
    assert "домик" in words
    assert "книга" in words


def test_normalize_word_success():
    assert wordly._normalize_word(" Домик ") == "домик"


@pytest.mark.parametrize(
    "value, message_substr",
    [
        ("", "cannot be empty"),
        ("   ", "cannot be empty"),
        ("abc", "only russian letters"),
        ("дом1к", "only russian letters"),
    ],
)
def test_normalize_word_invalid(value, message_substr):
    with pytest.raises(wordly.InvalidGuessError) as exc:
        wordly._normalize_word(value)
    assert message_substr in str(exc.value)


def test_build_feedback_basic():
    # target: домик, guess: домик → все correct
    target = "домик"
    guess = "домик"
    feedback = wordly._build_feedback(target, guess)
    assert all(item["result"] == "correct" for item in feedback)


def test_build_feedback_present_and_absent():
    # target: домик, guess: кимоД (перестановка и разные буквы)
    target = "домик"
    guess = "кимод"
    feedback = wordly._build_feedback(target, guess)

    # Проверяем, что длины совпадают и в ответе есть только допустимые маркеры
    assert len(feedback) == len(guess)
    for item in feedback:
        assert item["result"] in ("correct", "present", "absent")


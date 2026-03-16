import random
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Literal, Optional

from database.database import Database


ResultType = Literal["correct", "present", "absent"]
GameStatus = Literal["in_progress", "won", "lost"]


@dataclass
class GuessResult:
    guess: str
    feedback: List[Dict[str, ResultType]]


@dataclass
class GameState:
    game_id: str
    user_id: int
    target_word: str
    max_attempts: int = 6
    status: GameStatus = "in_progress"
    attempts: List[GuessResult] = field(default_factory=list)


_GAMES: Dict[str, GameState] = {}
_WORDS: Optional[List[str]] = None


async def _load_words() -> List[str]:
    """
    Загружает список допустимых слов из таблицы wordly_words.
    Если таблица или БД недоступны, используется файл static/wordly_words_ru.txt,
    а затем встроенный fallback список. Все слова приводятся к нижнему регистру
    и фильтруются по длине 5 символов.
    """
    fallback = [
        "домик",
        "книга",
        "мосты",
        "школа",
        "рекад",
        "листы",
        "окноо",
        "город",
        "берег",
    ]

    words: List[str] = []

    try:
        async with Database() as db:
            rows = await db.execute_all(
                "SELECT word FROM wordly_words WHERE active = true ORDER BY id",
                (),
            )
        if rows:
            words = [str(row["word"]).strip().lower() for row in rows if row.get("word")]
    except Exception:
        words = []

    if not words:
        base_dir = Path(__file__).resolve().parent.parent
        path = base_dir / "static" / "wordly_words_ru.txt"
        try:
            raw = path.read_text(encoding="utf-8").splitlines()
            words = [w.strip().lower() for w in raw if w.strip()]
        except OSError:
            words = []

    if not words:
        words = fallback

    filtered = [w for w in words if len(w) == 5]
    if not filtered:
        filtered = [w for w in fallback if len(w) == 5]
    return filtered


async def _ensure_words_loaded() -> List[str]:
    global _WORDS
    if _WORDS is None:
        _WORDS = await _load_words()
    return _WORDS


class GameNotFoundError(Exception):
    pass


class GameFinishedError(Exception):
    pass


class InvalidGuessError(Exception):
    pass


def _normalize_word(word: str) -> str:
    value = word.strip().lower()
    if not value:
        raise InvalidGuessError("guess cannot be empty")
    allowed = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    if any(ch not in allowed for ch in value):
        raise InvalidGuessError("guess must contain only russian letters а-я")
    return value


async def start_game(user_id: int) -> dict:
    """Создаёт новую игру и возвращает начальное состояние."""
    words = await _ensure_words_loaded()
    target = random.choice(words)
    game_id = str(uuid.uuid4())
    state = GameState(game_id=game_id, user_id=user_id, target_word=target)
    _GAMES[game_id] = state
    return {
        "game_id": game_id,
        "word_length": len(target),
        "max_attempts": state.max_attempts,
        "status": state.status,
        "attempts_made": 0,
    }


def _check_game_exists(game_id: str) -> GameState:
    game = _GAMES.get(game_id)
    if not game:
        raise GameNotFoundError("game not found")
    return game


def _build_feedback(target: str, guess: str) -> List[Dict[str, ResultType]]:
    result: List[Dict[str, ResultType]] = []
    target_chars = list(target)
    guess_chars = list(guess)

    marks: List[ResultType] = ["absent"] * len(guess_chars)
    for idx, ch in enumerate(guess_chars):
        if idx < len(target_chars) and ch == target_chars[idx]:
            marks[idx] = "correct"
            target_chars[idx] = "_"

    for idx, ch in enumerate(guess_chars):
        if marks[idx] == "correct":
            continue
        if ch in target_chars:
            marks[idx] = "present"
            target_chars[target_chars.index(ch)] = "_"

    for ch, m in zip(guess_chars, marks):
        result.append({"letter": ch, "result": m})
    return result


async def make_guess(game_id: str, raw_guess: str, user_id: int) -> dict:
    """Обрабатывает попытку и возвращает ответ для клиента."""
    game = _check_game_exists(game_id)
    if game.user_id != user_id:
        raise GameNotFoundError("game not found")
    if game.status != "in_progress":
        raise GameFinishedError("game already finished")

    guess = _normalize_word(raw_guess)
    if len(guess) != len(game.target_word):
        raise InvalidGuessError(f"guess length must be {len(game.target_word)}")

    feedback = _build_feedback(game.target_word, guess)
    game.attempts.append(GuessResult(guess=guess, feedback=feedback))

    is_win = guess == game.target_word
    if is_win:
        game.status = "won"
    elif len(game.attempts) >= game.max_attempts:
        game.status = "lost"
    if game.status in ("won", "lost"):
        winners_flag = game.status == "won"
        try:
            async with Database() as db:
                await db.execute(
                    """
                    INSERT INTO user_winners (user_id, winners)
                    VALUES ($1, $2)
                    ON CONFLICT (user_id) DO UPDATE
                    SET winners = EXCLUDED.winners
                    """,
                    (user_id, winners_flag),
                )
        except Exception:
            pass

    return {
        "game_id": game.game_id,
        "guess": guess,
        "feedback": feedback,
        "attempt": len(game.attempts),
        "remaining_attempts": max(game.max_attempts - len(game.attempts), 0),
        "status": game.status,
        "is_win": is_win,
        "is_finished": game.status in ("won", "lost"),
        "target_word_revealed": game.target_word if game.status == "lost" else None,
    }


async def get_state(game_id: str, user_id: int) -> dict:
    """Возвращает текущее состояние игры по game_id."""
    game = _check_game_exists(game_id)
    if game.user_id != user_id:
        raise GameNotFoundError("game not found")
    return {
        "game_id": game.game_id,
        "word_length": len(game.target_word),
        "max_attempts": game.max_attempts,
        "status": game.status,
        "attempts_made": len(game.attempts),
        "attempts": [
            {
                "guess": attempt.guess,
                "feedback": attempt.feedback,
                "attempt": idx + 1,
            }
            for idx, attempt in enumerate(game.attempts)
        ],
        "target_word_revealed": game.target_word if game.status == "lost" else None,
    }


async def get_user_status(user_id: int) -> dict:
    """
    Возвращает агрегированный статус пользователя по игре T-Word:
    - played: есть ли запись в user_winners (то есть пользователь завершал хотя бы одну игру);
    - winners: значение флага winners из таблицы (выигрывал ли он хотя бы раз).
    При отсутствии таблицы или записи возвращаем played = False, winners = False.
    """
    try:
        async with Database() as db:
            row = await db.execute(
                "SELECT winners FROM user_winners WHERE user_id = $1::bigint",
                (user_id,),
            )
    except Exception:
        # При проблемах с БД не блокируем фронт, возвращаем «не играл / не выиграл»
        return {
            "played": False,
            "winners": False,
        }

    if row is None:
        return {
            "played": False,
            "winners": False,
        }

    return {
        "played": True,
        "winners": bool(row.get("winners")),
    }


"""
Юнит-тесты для офферов и прогресса.

Модули functions.offers и functions.progress в текущей кодовой базе отсутствуют:
логика офферов реализована в api/calculate.py (использует functions.calculate),
прогресс — в api/progress.py (заглушка). Эти тесты пропущены до появления
соответствующих модулей в functions/.
"""

import pytest


@pytest.mark.skip(reason="functions.offers не существует; используется api/calculate + functions.calculate")
class TestOffersFunctions:
    pass


@pytest.mark.skip(reason="functions.progress не существует; используется api/progress (заглушка)")
class TestProgressFunctions:
    pass

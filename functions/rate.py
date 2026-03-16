def calc_rate(budget_amount: int) -> dict:
    """
    budget_amount бюджет на одного пользователя по категории за период.
    Ставка считается как доля среднего чека пользователя, но сам средний чек
    сейчас не хранится в БД, поэтому используем только бюджет на пользователя.
    """
    try:
        if not budget_amount or budget_amount <= 0:
            return {"min": 5, "max": 15}

        base_rate = max(1, min(30, round(budget_amount / 100)))

        return {
            "min": max(1, base_rate - 2),
            "max": min(30, base_rate + 2),
        }
    except Exception:
        return {"min": 5, "max": 15}

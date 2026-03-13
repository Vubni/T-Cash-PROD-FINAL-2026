"""Расчёт диапазона ставки кэшбэка по бюджету и ожидаемым тратам."""


def calc_rate(
    budget_amount: int,
    target_users: int,
    avg_spend_per_user: int,
) -> dict:
    """Вычисляет min/max ставку (в процентах) по бюджету и целевой аудитории."""
    try:
        if not budget_amount or not target_users or not avg_spend_per_user:
            return {"min": 5, "max": 15}
        total_expected_spend = target_users * avg_spend_per_user
        if total_expected_spend <= 0:
            return {"min": 5, "max": 15}
        base_rate = round(100 * budget_amount / total_expected_spend)
        base_rate = max(1, min(base_rate, 30))
        return {
            "min": max(1, base_rate - 2),
            "max": min(30, base_rate + 2),
        }
    except Exception:
        return {"min": 5, "max": 15}

import aiohttp
from database.database import Database
from config import CALC_SERVICE_URL, logger
from core import serialize_json, FALLBACK_CATEGORY_NAMES, get_all_categories

_offers_run_cache: dict[int, list[dict]] = {}


def get_offers_run_cache(user_id: int) -> list[dict] | None:
    """Возвращает закэшированный результат offers/run для user_id или None."""
    return _offers_run_cache.get(user_id)


def _set_offers_run_cache(user_id: int, items: list[dict]) -> None:
    """Сохраняет в кэш по user_id только поля category_id, cashback, estimated_spend, name, subtitle."""
    _offers_run_cache[user_id] = [
        {
            "category_id": it.get("category_id"),
            "cashback": it.get("cashback"),
            "estimated_spend": it.get("estimated_spend"),
            "name": it.get("name"),
            "subtitle": it.get("subtitle"),
        }
        for it in items
    ]


async def get_calculate_items(user_id: int) -> dict:
    items = []
    async with Database() as db:
        sql = """
            SELECT
                s.selection_id,
                s.category_id,
                c.name,
                c.subtitle,
                c.icon_path,
                c.rate_min,
                c.rate_max
            FROM selections s
            JOIN categories c ON c.category_id = s.category_id
            WHERE s.user_id = $1::bigint
              AND c.status = 'running'
        """
        rows = await db.execute_all(sql, (user_id,)) or []

    if rows:
        items_serialized = serialize_json(rows)
        _set_offers_run_cache(
            user_id,
            [
                {
                    "category_id": r["category_id"],
                    "cashback": r.get("rate_min"),
                    "estimated_spend": None,
                    "name": r["name"],
                    "subtitle": r.get("subtitle"),
                }
                for r in rows
            ],
        )
        return {"items": items_serialized, "already_selected_categories": True}

    async with Database() as db:
        sql = """
            SELECT
                c.category_id,
                c.name,
                c.subtitle,
                c.icon_path,
                c.rate_min,
                c.rate_max
            FROM categories c
            LEFT JOIN rules r ON r.rule_id = c.rule_id
            LEFT JOIN users u ON u.user_id = $1::bigint
            WHERE c.status = 'running'
              AND (
                c.rule_id IS NULL
                OR (
                  (r.min_age IS NULL OR u.age >= r.min_age)
                  AND (r.max_age IS NULL OR u.age <= r.max_age)
                  AND (r.gender IS NULL OR u.gender = r.gender)
                  AND (r.income IS NULL OR u.income >= r.income)
                )
              )
        """
        categories = await db.execute_all(sql, (user_id,)) or []
        category_names = [c["name"] for c in categories]
        if not category_names:
            category_names = FALLBACK_CATEGORY_NAMES

        logger.info("Calculating categories for user %s: %s", user_id, category_names)
        payload = {
            "categories": category_names,
            "client_id": str(user_id),
            "top_n": max(1, get_all_categories() + 1),
        }
        logger.info(
            "Calculate request: url=%s categories_count=%s client_id=%s top_n=%s",
            f"{CALC_SERVICE_URL.rstrip('/')}/predict",
            len(payload["categories"]),
            user_id,
            payload["top_n"],
        )
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{CALC_SERVICE_URL.rstrip('/')}/predict",
                json=payload,
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(
                        "Calculate failed: status=%s url=%s body=%s",
                        response.status,
                        response.url,
                        text[:2000] if text else "(empty)",
                    )
                    raise Exception(f"Failed to calculate: {response.status} {text}")
                data = await response.json()
        predictions = data["predictions"]

    async with Database() as db:
        for predict in predictions:
            category = await db.execute("SELECT * FROM categories WHERE name = $1", (predict["category"],))
            if not category:
                logger.error("Category not found: %s", predict.get("category"))
                continue
            estimated = predict.get("estimated_spend") or 0
            if estimated <= 0:
                continue
            percent = int(category["budget_amount"] * 100 / estimated)
            logger.info("Category: %s, Estimated: %s, Percent: %s", category["budget_amount"], estimated, percent)
            items.append(
                {
                    "category_id": category["category_id"],
                    "name": category["name"],
                    "subtitle": category["subtitle"],
                    "cashback": max(category["rate_min"], min(category["rate_max"], percent)),
                    "reasons": predict.get("reasons", []),
                    "estimated_spend": predict.get("estimated_spend")
                }
            )

    _set_offers_run_cache(user_id, items)
    return {"items": serialize_json(items), "already_selected_categories": False}

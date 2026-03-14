import aiohttp
from database.database import Database
from core import serialize_json
from core import get_all_categories, get_max_selection_count, logger
from config import ML_SERVICE_URL


async def get_calculate_items(user_id: int) -> list[dict]:
    items = []
    async with Database() as db:
        sql = """
            SELECT
                s.selection_id,
                s.category_id,
                c.name,
                c.subtitle,
                c.rate_min,
                c.rate_max
            FROM selections s
            JOIN categories c ON c.category_id = s.category_id
            WHERE s.user_id = $1::bigint
        """
        rows = await db.execute_all(sql, (user_id,)) or []

    if rows:
        return serialize_json(rows)

    async with Database() as db:
        sql = """
            SELECT
                category_id,
                name,
                subtitle,
                rate_min,
                rate_max
            FROM categories LIMIT $1
        """
        categories = await db.execute_all(sql, (get_all_categories(),)) or []
        category_names = [c["name"] for c in categories]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{ML_SERVICE_URL.rstrip('/')}/predict",
                json={
                    "categories": category_names,
                    "client_id": str(user_id),
                    "top_n": max(1, get_max_selection_count()),
                },
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(
                        "ML predict failed: status=%s url=%s body=%s",
                        response.status,
                        response.url,
                        text[:2000] if text else "",
                    )
                    raise Exception(f"Failed to calculate: {response.status} {text}")
                data = await response.json()
        predictions = data["predictions"]

        for predict in predictions:
            category = await db.execute("SELECT * FROM categories WHERE name = $1", (predict["category"],))
            if not category:
                logger.error("Category not found: %s", predict.get("category"))
                continue
            estimated = predict.get("estimated_spend") or 0
            if estimated <= 0:
                continue
            percent = int(category["budget_amount"] * 100 / estimated)
            items.append(
                {
                    "category_id": category["category_id"],
                    "name": category["name"],
                    "subtitle": category["subtitle"],
                    "cashback": max(category["rate_min"], min(category["rate_max"], percent)),
                }
            )

    return serialize_json(items)

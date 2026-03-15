import aiohttp
from database.database import Database
from core import serialize_json, ML_CATEGORY_NAMES, logger
from core import get_all_categories
from config import ML_SERVICE_URL


async def get_calculate_items(user_id: int) -> dict:
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
        return {"items": serialize_json(rows), "already_selected_categories": True}

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
        if not category_names:
            category_names = ML_CATEGORY_NAMES

        payload = {
            "categories": ML_CATEGORY_NAMES,
            "client_id": str(user_id),
            "top_n": max(1, get_all_categories()),
        }
        logger.info(
            "ML predict request: url=%s categories_count=%s client_id=%s top_n=%s",
            f"{ML_SERVICE_URL.rstrip('/')}/predict",
            len(category_names),
            user_id,
            payload["top_n"],
        )
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{ML_SERVICE_URL.rstrip('/')}/predict",
                json=payload,
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(
                        "ML predict failed: status=%s url=%s body=%s",
                        response.status,
                        response.url,
                        text[:2000] if text else "(empty)",
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
            logger.info("Category: %s, Estimated: %s, Percent: %s", category["name"], estimated, percent)
            items.append(
                {
                    "category_id": category["category_id"],
                    "name": category["name"],
                    "subtitle": category["subtitle"],
                    "cashback": max(category["rate_min"], min(category["rate_max"], percent)),
                    "reasons": predict.get("reasons", [])
                }
            )

    return {"items": serialize_json(items), "already_selected_categories": False}

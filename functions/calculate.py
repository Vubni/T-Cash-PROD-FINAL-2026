import aiohttp
from database.database import Database
from config import CALC_SERVICE_URL, logger
from core import serialize_json, FALLBACK_CATEGORY_NAMES, get_all_categories
from functions.wordly import get_user_status

_offers_run_cache: dict[int, list[dict]] = {}


def get_offers_run_cache(user_id: int) -> list[dict] | None:
    """Возвращает закэшированный результат offers/run для user_id или None."""
    return _offers_run_cache.get(user_id)


def _set_offers_run_cache(user_id: int, items: list[dict]) -> None:
    """Сохраняет в кэш по user_id поля category_id, cashback, estimated_spend, name, subtitle, icon_url."""
    _offers_run_cache[user_id] = [
        {
            "category_id": it.get("category_id"),
            "cashback": it.get("cashback"),
            "estimated_spend": it.get("estimated_spend"),
            "name": it.get("name"),
            "subtitle": it.get("subtitle"),
            "icon_url": it.get("icon_url"),
        }
        for it in items
    ]


async def get_calculate_items(user_id: int) -> dict:
    async with Database() as db:
        sql = """
            SELECT
                s.selection_id,
                s.category_id,
                s.cashback,
                s.estimated_spend,
                c.name,
                c.subtitle,
                c.icon_url,
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
                    "cashback": r.get("cashback") if r.get("cashback") is not None else r.get("rate_min"),
                    "estimated_spend": r.get("estimated_spend"),
                    "name": r["name"],
                    "subtitle": r.get("subtitle"),
                    "icon_url": r.get("icon_url"),
                }
                for r in rows
            ],
        )
        return {
            "items": items_serialized,
            "already_selected_categories": True,
            "has_bonus_category": False,
        }

    items: list[dict] = []
    user_status = await get_user_status(user_id=user_id)
    is_tword_winner = bool(user_status.get("winners"))

    async with Database() as db:
        sql = """
            SELECT
                c.category_id,
                c.name,
                c.subtitle,
                c.icon_url,
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
        base_top_n = max(1, get_all_categories())
        top_n = base_top_n + 1 if is_tword_winner else base_top_n
        payload = {
            "categories": category_names,
            "client_id": str(user_id),
            "top_n": top_n,
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
            ITEMS_REASONS = {
                # Базовые причины
                "У клиента уже была недавняя активность в этой категории за последние 3 месяца": "RecentCategoryActivity_3M",
                "Категория находится среди лидеров по внутреннему offer score для этого клиента": "HighOfferScoreCategory",
                "История клиента по этой категории лучше среднего по категории": "CustomerAboveCategoryAvg",
                "Категория исторически сильнее работает в сегменте пола и возраста клиента": "StrongInDemographicSegment",
                "Категория занимает заметную долю в недавнем обороте клиента": "HighShareInRecentTurnover",
                "Для части признаков использован последний доступный исторический срез по клиенту": "UsedLatestAvailableSnapshot",
                "Категория выбрана по совокупности исторических паттернов клиента и глобального спроса": "SelectedByPatternsAndDemand",
                # Если категория mapped
                "Категория сопоставлена с модельной категорией '...'": "MappedToModelCategory",
                "Источник нормализации категории: alias": "CategorySourceAlias",
                "Источник нормализации категории: llm": "CategorySourceLLM",
                "Источник нормализации категории: embedding": "CategorySourceEmbedding",
                "Источник нормализации категории: heuristic": "CategorySourceHeuristic",
                "Для сопоставления была использована локальная LLM для подбора ближайшей канонической категории": "LocalLLMForMapping",
                # Если категория novel
                "Категория новая для основной модели и оценена через low-level novel-category логику": "NovelCategoryLowLevelLogic",
                "Для оценки использованы история клиента и ближайшая каноническая категория в embedding-пространстве": "NovelCategoryWithNearestEmbedding",
                "Ближайшая каноническая категория: '...' (similarity=...)": "NearestCanonicalCategoryInfo",
                # Если категория fallback
                "Категория отсутствует в тренировочном словаре модели и оценена через консервативную fallback-логику": "FallbackLogicUsed",
                "Во fallback использованы общая склонность клиента к активации и слабый embedding-сосед": "FallbackWithWeakNeighbor",
                "Слабый ближайший сосед в embedding-пространстве: '...' (similarity=...)": "WeakNearestNeighborInfo",
                # Если категория совсем непонятная и идёт отказ
                "Категория слишком непонятная для надежного сопоставления и поэтому получила score=0": "RejectedCategoryScoreZero",
                "Ни alias, ни LLM, ни embedding similarity не дали достаточно уверенного соответствия": "RejectedNoConfidentMatch",
                "Backend может безопасно обработать категорию '...' как отказ ML-слоя": "BackendSafeReject",
                # Если сервис ушёл в резервный режим
                "Основная модель временно недоступна, поэтому сервис перешел в резервный режим с популярными категориями": "ReserveModeEnabled",
                "Категория выбрана из популярного fallback-каталога (global_category_history)": "FromPopularFallbackCatalog",
                "Причина деградации: ...": "DegradationReasonInfo",
            }
            items.append(
                {
                    "category_id": category["category_id"],
                    "name": category["name"],
                    "subtitle": category["subtitle"],
                    "icon_url": category.get("icon_url"),
                    "cashback": max(category["rate_min"], min(category["rate_max"], percent)),
                    "reasons": [ITEMS_REASONS.get(reason) for reason in predict.get("reasons", [])],
                    "estimated_spend": predict.get("estimated_spend"),
                }
            )

    _set_offers_run_cache(user_id, items)
    return {
        "items": serialize_json(items),
        "already_selected_categories": False,
        "has_bonus_category": is_tword_winner,
    }

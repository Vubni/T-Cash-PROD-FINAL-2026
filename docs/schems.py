from marshmallow import Schema, fields

class TokenResponseSchema(Schema):
    token = fields.Str(description="Токен для взаимодействия с аккаунтом")

class UserAuthSchema(Schema):
    identifier = fields.Str(required=True)
    password = fields.Str(required=True)
    
class UserProfileSchema(Schema):
    login = fields.Str()
    email = fields.Str()
    name = fields.Str()
    surname = fields.Str()
    class_number = fields.Int()
    class_letter = fields.Str()
    telegram_name = fields.Str()
    
class LoginEditSchema(Schema):
    login = fields.Str(required=True, description="login пользователя. До 20 символов")
    
class EmailEditSchema(Schema):
    email = fields.Str(required=True, description="email пользователя. До 256 символов")
    
class PasswordEditSchema(Schema):
    current_password = fields.Str(required=True, description="password пользователя.")
    new_password = fields.Str(required=True, description="password пользователя.")
    
class TelegramConnectSchema(Schema):
    url = fields.Str(required=True, description="Ссылка для привязки аккаунта Telegram.")
    
class EmailVerifyConfirmSchema(Schema):
    token = fields.Str(required=True)
    

class ScheduleGetSchema(Schema):
    date = fields.Date(required=True, description="Дата на которую получают расписание.")
    
class ClubsListSchema(Schema):
    type = fields.Str(default="my")
    offset = fields.Int(default=0)
    limit = fields.Int(default=100)
    
class ClubGetSchema(Schema):
    club_id = fields.Int(required=True, description="id клуба")
    
class ClubNewSchema(Schema):
    title = fields.Str(required=True, description="Название клуба. До 20 символов")
    description = fields.Str(required=True, description="Описание клуба. До 200 символов")
    administration = fields.Int(required=True, description="Направление клуба (ответственное министерство)")
    max_members_counts = fields.Int(required=True, description="Максимальное количество участников клуба", default=0)
    class_limit_min = fields.Int(required=True, description="Минимальный класс для участия в клубе", default=1)
    class_limit_max = fields.Int(required=True, description="Максимальный класс для участия в клубе", default=11)
    telegram_url = fields.Str(required=True, description="URL телеграм-канала клуба")
    
class CheckTitleSchema(Schema):
    title = fields.Str(required=True, description="Название клуба")
    
class AdministrationListSchema(Schema):
    id = fields.Int()
    title = fields.Str()

class ScheduleItemSchema(Schema):
    start_time = fields.Str(required=True, description="Время начала урока в формате ЧЧ:ММ")
    stop_time = fields.Str(required=True, description="Время окончания урока в формате ЧЧ:ММ")
    lesson_number = fields.Int(required=True, description="Порядковый номер урока")
    title = fields.Str(
        required=False, 
        allow_none=True, 
        description="Название урока (присутствует только если урок запланирован)"
    )
    classrooms = fields.List(
        fields.Raw(), 
        required=False, 
        allow_none=True, 
        description="Список кабинетов (строки/числа) или None"
    )
    teachers = fields.List(
        fields.Str(), 
        required=False, 
        allow_none=True, 
        description="Список преподавателей (строки) или None"
    )
    
class ClubSchema(Schema):
    id = fields.Int(required=True, description="ID клуба")
    title = fields.Str(required=True, description="Название клуба")
    members_count = fields.Int(required=True, description="Количество участников клуба")
    max_members_counts = fields.Int(required=True, description="Максимальное количество участников клуба")
    class_limit_min = fields.Int(required=True, description="Минимальный класс для участия в клубе")
    class_limit_max = fields.Int(required=True, description="Максимальный класс для участия в клубе")
    
    
class ClubGetReturnSchema(Schema):
    id = fields.Int(required=True, description="ID клуба")
    title = fields.Str(required=True, description="Название клуба")
    description = fields.Str(required=True, description="Описание клуба")
    telegram_url = fields.Str(required=True, description="Ссылка на Telegram-канал/группу клуба")
    xp = fields.Int(required=True, description="Текущий опыт клуба")
    members_count = fields.Int(required=True, description="Количество участников клуба")
    max_members_counts = fields.Int(required=True, description="Максимальное количество участников клуба")
    administration = fields.Int(required=True, description="Направление клуба (ответственное министерство)")
    class_limit_min = fields.Int(required=True, description="Минимальный класс для участия в клубе")
    class_limit_max = fields.Int(required=True, description="Максимальный класс для участия в клубе")
    participant = fields.Bool(required=True, description="Является ли пользователь участником клуба")
    admin = fields.Bool(required=True, description="Является ли пользователь администратором клубa")

    
class ClubJoinSchema(Schema):
    club_id = fields.Int(required=True, description="id клуба")

class AchievementsLocalSchema(Schema):
    club_id = fields.Int(required=True, description="id клуба")

class ClubEditSchema(Schema):
    club_id = fields.Int(required=True, description="id клуба")
    title = fields.Str(required=True, description="Название клуба")
    description = fields.Str(required=True, description="Описание клуба")
    max_members_counts = fields.Int(required=True, description="Максимальное количество участников в клубе")
    class_limit_min = fields.Int(required=True, description="Минимальный класс для участия в клубе")
    class_limit_max = fields.Int(required=True, description="Максимальный класс для участия в клубе")
    telegram_url = fields.Str(required=True, description="Telegram ссылка на канал/группу клуба")
    

class AchievementsGlobalReturnSchema(Schema):
    title = fields.Str(description="Название достижения")
    description = fields.Str(description="Описание достижения")
    xp = fields.Str(description="Текущий набранный опыт")
    need_xp = fields.Str(description="Необходимый опыт")

class TeachersSchema(Schema):
    name = fields.Str(description="ФИО учителя")
    subject = fields.Str(description="Предмет, который ведёт")

class AchievementsSchema(Schema):
    title = fields.Str(description="Название достижения")
    description = fields.Str(description="Описание достижения")
    image_path = fields.Str(description="Путь к изображению достижения")
    date = fields.Date(description="Дата события")
    url = fields.Str(description="Ссылка на основную информацию новости или т.п.")

class TelegramAuthSchema(Schema):
    url = fields.Str(description="Ссылка на тг бота")
    token = fields.Str(description="Токен для проверки прошла ли авторизация в боте")

class ForgotPasswordSchema(Schema):
    identifier = fields.Str(required=True, description="Логин или email пользователя")
    new_password = fields.Str(required=True, description="Новый пароль пользователя")

class ForgotPasswordConfirmSchema(Schema):
    confirm = fields.Int(required=True)


    
class ErrorDetailSchema(Schema):
    name = fields.Str(description="Имя параметра, вызвавшего ошибку")
    type = fields.Str(description="Тип ошибки (например, missing)")
    message = fields.Str(description="Сообщение об ошибке")
    value = fields.Raw(description="Значение параметра, если оно было передано", allow_none=True)


class FieldErrorItemSchema(Schema):
    field = fields.Str(description="Поле с ошибкой")
    issue = fields.Str(description="Описание ошибки")
    rejectedValue = fields.Raw(allow_none=True, description="Отклонённое значение")


class HttpErrorSchema(Schema):
    code = fields.Str(description="Код ошибки (UNAUTHORIZED, FORBIDDEN, NOT_FOUND, ...)")
    message = fields.Str(description="Сообщение об ошибке")
    traceId = fields.Str(description="Идентификатор запроса для отладки")
    timestamp = fields.Str(description="Время ответа в ISO 8601")
    path = fields.Str(description="Путь запроса")
    details = fields.Dict(allow_none=True, description="Дополнительные данные (опционально)")
    fieldErrors = fields.List(
        fields.Nested(FieldErrorItemSchema),
        allow_none=True,
        description="Ошибки по полям при 422 (опционально)",
    )


RESPONSES_HTTP_ERROR = {
    400: {"description": "Некорректный запрос", "schema": HttpErrorSchema},
    401: {"description": "Не авторизован", "schema": HttpErrorSchema},
    403: {"description": "Нет прав", "schema": HttpErrorSchema},
    404: {"description": "Не найдено", "schema": HttpErrorSchema},
    409: {"description": "Конфликт (дубликат и т.п.)", "schema": HttpErrorSchema},
    422: {"description": "Ошибка валидации", "schema": HttpErrorSchema},
    500: {"description": "Внутренняя ошибка сервера", "schema": HttpErrorSchema},
}


class Error400Schema(Schema):
    error = fields.Str(description="Общее сообщение об ошибке")
    errors = fields.List(fields.Nested(ErrorDetailSchema), description="Список детальных ошибок")
    received_params = fields.Dict(description="Параметры, которые были успешно получены")


class AlreadyBeenTaken(Schema):
    name = fields.Str(description="Название переменной, которая занята")
    error = fields.Str(description="Описание, что переменная занята")


class CategoryAudienceSchema(Schema):
    segments = fields.List(
        fields.Str(),
        required=True,
        description="Список сегментов аудитории, для которых категория доступна",
    )


class CategoryBudgetSchema(Schema):
    amount = fields.Float(required=True, description="Бюджет категории на период")


class CategoryRateSchema(Schema):
    min = fields.Float(required=True, description="Минимальная ставка кэшбэка")
    max = fields.Float(required=True, description="Максимальная ставка кэшбэка")


class CategoryRuleSchema(Schema):
    personalized = fields.Bool(
        required=True,
        description="Признак, что категория участвует в персональном ранжировании",
    )
    budget_mode = fields.Str(
        required=True,
        description="Режим контроля бюджета, например hard_limit или soft_limit",
    )
    fallback_message = fields.Str(
        required=True,
        description="Текст, который можно показать пользователю, если категория недоступна",
    )


class CategoryHistoryItemSchema(Schema):
    changed_at = fields.Str(required=True, description="Дата и время изменения в ISO 8601")
    changed_by = fields.Str(required=True, description="Кто изменил категорию")
    field = fields.Str(required=True, description="Какое поле изменили")
    old_value = fields.Raw(required=False, allow_none=True, description="Старое значение")
    new_value = fields.Raw(required=False, allow_none=True, description="Новое значение")


class CategoryListItemSchema(Schema):
    id = fields.Str(required=True, description="Идентификатор категории")
    name = fields.Str(required=True, description="Название категории")
    subtitle = fields.Str(required=True, description="Подзаголовок категории")
    icon_key = fields.Str(required=True, description="Ключ иконки категории")
    icon_url = fields.Str(required=False, description="Путь до иконки категории")
    budget = fields.Nested(CategoryBudgetSchema, required=True)
    rate = fields.Nested(CategoryRateSchema, required=True)


class CategoryDetailSchema(Schema):
    id = fields.Str(required=True, description="Идентификатор категории")
    name = fields.Str(required=True, description="Название категории")
    subtitle = fields.Str(required=True, description="Подзаголовок категории")
    icon_key = fields.Str(required=True, description="Ключ иконки категории")
    icon_url = fields.Str(required=False, description="Путь до иконки категории")
    budget = fields.Nested(CategoryBudgetSchema, required=True)
    rate = fields.Nested(CategoryRateSchema, required=True)
    audience = fields.Nested(CategoryAudienceSchema, required=True)
    rule = fields.Nested(CategoryRuleSchema, required=True)
    history = fields.List(
        fields.Nested(CategoryHistoryItemSchema),
        required=True,
        description="История изменений категории",
    )


class CategoryListResponseSchema(Schema):
    items = fields.List(
        fields.Nested(CategoryListItemSchema),
        required=True,
        description="Список категорий",
    )
    total = fields.Int(required=True, description="Общее количество категорий (для пагинации)")


class CategoryCreateSchema(Schema):
    name = fields.Str(required=True, description="Название категории")
    subtitle = fields.Str(required=True, description="Подзаголовок категории")
    icon_key = fields.Str(required=True, description="Ключ иконки категории")
    budget_amount = fields.Float(required=True, description="Бюджет категории на период")
    rate_min = fields.Float(required=True, description="Минимальная ставка кэшбэка")
    rate_max = fields.Float(required=True, description="Максимальная ставка кэшбэка")
    audience_segments = fields.List(
        fields.Str(),
        required=True,
        description="Сегменты аудитории категории",
    )
    rule_personalized = fields.Bool(
        required=True,
        description="Участвует ли категория в персональном подборе",
    )
    rule_budget_mode = fields.Str(
        required=True,
        description="Режим бюджетного контроля для категории",
    )
    rule_fallback_message = fields.Str(
        required=True,
        description="Сообщение для пользователя, если категория недоступна",
    )


class CategoryUpdateSchema(Schema):
    name = fields.Str(required=False, description="Новое название категории")
    subtitle = fields.Str(required=False, description="Новый подзаголовок категории")
    icon_key = fields.Str(required=False, description="Новый ключ иконки категории")
    budget_amount = fields.Float(required=False, description="Новый бюджет категории")
    rate_min = fields.Float(required=False, description="Новая минимальная ставка кэшбэка")
    rate_max = fields.Float(required=False, description="Новая максимальная ставка кэшбэка")
    audience_segments = fields.List(
        fields.Str(),
        required=False,
        description="Новый список сегментов аудитории",
    )
    rule_personalized = fields.Bool(required=False, description="Новый флаг персонализации")
    rule_budget_mode = fields.Str(required=False, description="Новый режим бюджетного контроля")
    rule_fallback_message = fields.Str(
        required=False,
        description="Новое fallback-сообщение для пользователя",
    )


class AuditEventSchema(Schema):
    id = fields.Str(required=True, description="Идентификатор события аудита")
    entity_type = fields.Str(required=True, description="Тип сущности")
    entity_id = fields.Str(required=True, description="Идентификатор сущности")
    action = fields.Str(required=True, description="Действие, например create или update")
    actor = fields.Str(required=True, description="Кто выполнил действие")
    created_at = fields.Str(required=True, description="Дата и время события в ISO 8601")


class AuditListResponseSchema(Schema):
    items = fields.List(
        fields.Nested(AuditEventSchema),
        required=True,
        description="Список событий аудита",
    )
    total = fields.Int(required=True, description="Количество событий в ответе")


class UserSchema(Schema):
    id = fields.Str(required=True, description="UUID пользователя")
    name = fields.Str(required=True, description="Имя пользователя")


class UserListResponseSchema(Schema):
    items = fields.List(
        fields.Nested(UserSchema),
        required=True,
        description="Список пользователей",
    )
    total = fields.Int(required=True, description="Количество")


class CalculateRequestSchema(Schema):
    user_id = fields.Str(required=True, description="UUID пользователя (выбор на фронте)")


class CalculateCategoryItemSchema(Schema):
    selection_id = fields.Str(
        required=False,
        allow_none=True,
        description="Идентификатор выбора (если уже сохранён) или null для варианта категории",
    )
    category_id = fields.Str(required=True, description="Идентификатор категории")
    name = fields.Str(required=True, description="Название категории")
    subtitle = fields.Str(required=True, description="Подзаголовок категории")
    icon_key = fields.Str(required=True, description="Ключ иконки категории")
    icon_url = fields.Str(required=False, description="Путь до иконки категории")
    rate = fields.Nested(CategoryRateSchema, required=True)
    expected_benefit_amount = fields.Float(
        required=False,
        allow_none=True,
        description="Ожидаемая выгода по категории (null если ещё не выбран)",
    )
    availability_status = fields.Str(
        required=False,
        allow_none=True,
        description="Статус доступности: available, budget_limited и т.д.",
    )
    availability_reason = fields.Str(
        required=False,
        allow_none=True,
        description="Пояснение, если категория ограничена или недоступна",
    )


class CalculateResponseSchema(Schema):
    user_id = fields.Str(required=True, description="Пользователь, для которого рассчитано")
    items = fields.List(
        fields.Nested(CalculateCategoryItemSchema),
        required=True,
        description="Категории/выборы для пользователя за период",
    )


class SelectionDetailSchema(Schema):
    selection_id = fields.Str(required=True, description="Идентификатор выбора")
    category_id = fields.Str(required=True, description="Идентификатор категории")
    name = fields.Str(required=True, description="Название категории")
    subtitle = fields.Str(required=True, description="Подзаголовок категории")
    icon_key = fields.Str(required=False, description="Ключ иконки категории")
    icon_url = fields.Str(required=False, description="Путь до иконки категории")
    rate = fields.Nested(CategoryRateSchema, required=True)
    expected_benefit_amount = fields.Float(
        required=True,
        description="Ожидаемая выгода пользователя по выбранной категории",
    )
    budget_message = fields.Str(
        required=False,
        allow_none=True,
        description="Сообщение о бюджетных ограничениях, если они есть",
    )


class SelectionConfirmSchema(Schema):
    confirm = fields.Bool(
        required=False,
        description="Флаг подтверждения выбора. По умолчанию true",
    )


class SelectionSubmitBodySchema(Schema):
    user_id = fields.Str(required=True, description="UUID пользователя")
    category_ids = fields.List(
        fields.Str(),
        required=True,
        description="Ровно 5 идентификаторов категорий (UUID)",
    )


class SelectionSubmitResponseSchema(Schema):
    selection_id = fields.Str(required=True, description="Идентификатор запроса (из path)")
    category_ids = fields.List(
        fields.Str(),
        required=True,
        description="Сохранённые 5 категорий",
    )
    selection_ids = fields.List(
        fields.Str(),
        required=True,
        description="Созданные selection_id для каждой из 5 строк",
    )
    message = fields.Str(required=True, description="Подтверждение сохранения")


class SelectionConfirmResponseSchema(Schema):
    selection_id = fields.Str(required=True, description="Идентификатор подтверждённого выбора")
    category_id = fields.Str(required=True, description="Идентификатор выбранной категории")
    expected_benefit_amount = fields.Float(
        required=True,
        description="Ожидаемая выгода после подтверждения выбора",
    )
    message = fields.Str(required=True, description="Комментарий backend по результату подтверждения")

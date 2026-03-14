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
    type = fields.Str(required=False, missing="my", description="Тип списка (по умолчанию my)")
    offset = fields.Int(required=False, missing=0, description="Смещение для пагинации (по умолчанию 0)")
    limit = fields.Int(required=False, missing=100, description="Лимит элементов (по умолчанию 100)")
    
class ClubGetSchema(Schema):
    club_id = fields.Int(required=True, description="id клуба")
    
class ClubNewSchema(Schema):
    title = fields.Str(required=True, description="Название клуба. До 20 символов")
    description = fields.Str(required=True, description="Описание клуба. До 200 символов")
    administration = fields.Int(required=True, description="Направление клуба (ответственное министерство)")
    max_members_counts = fields.Int(required=False, missing=0, description="Максимальное количество участников клуба (по умолчанию 0)")
    class_limit_min = fields.Int(required=False, missing=1, description="Минимальный класс для участия в клубе (по умолчанию 1)")
    class_limit_max = fields.Int(required=False, missing=11, description="Максимальный класс для участия в клубе (по умолчанию 11)")
    telegram_url = fields.Str(required=False, allow_none=True, missing=None, description="URL телеграм-канала клуба (опционально)")
    
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
        description="Список сегментов аудитории, для которых категория доступна. Обязательное поле.",
    )


class CategoryBudgetSchema(Schema):
    amount = fields.Float(
        required=True,
        description="Бюджет на одного пользователя по категории за период. Обязательное поле.",
    )


class CategoryRateSchema(Schema):
    min = fields.Float(required=True, description="Минимальная ставка кэшбэка. Обязательное поле.")
    max = fields.Float(required=True, description="Максимальная ставка кэшбэка. Обязательное поле.")


class CategoryRuleSchema(Schema):
    rule_id = fields.Str(required=True, description="Идентификатор правила отбора. Обязательное поле.")
    min_age = fields.Int(allow_none=True, description="Минимальный возраст. Опционально.")
    max_age = fields.Int(allow_none=True, description="Максимальный возраст. Опционально.")
    gender = fields.Str(allow_none=True, description="Пол. Опционально.")
    income = fields.Int(allow_none=True, description="Заработок. Опционально.")


class CategoryHistoryItemSchema(Schema):
    changed_at = fields.Str(required=True, description="Дата и время изменения в ISO 8601. Обязательное поле.")
    changed_by = fields.Str(required=True, description="Кто изменил категорию. Обязательное поле.")
    field = fields.Str(required=True, description="Какое поле изменили. Обязательное поле.")
    old_value = fields.Raw(required=False, allow_none=True, description="Старое значение. Опционально.")
    new_value = fields.Raw(required=False, allow_none=True, description="Новое значение. Опционально.")


class CategoryListItemSchema(Schema):
    id = fields.Str(required=True, description="Идентификатор категории. Обязательное поле.")
    name = fields.Str(required=True, description="Название категории. Обязательное поле.")
    subtitle = fields.Str(required=True, description="Подзаголовок категории. Обязательное поле.")
    budget = fields.Nested(CategoryBudgetSchema, required=True)
    rate = fields.Nested(CategoryRateSchema, required=True)


class CategoryDetailSchema(Schema):
    id = fields.Str(required=True, description="Идентификатор категории. Обязательное поле.")
    name = fields.Str(required=True, description="Название категории. Обязательное поле.")
    subtitle = fields.Str(required=True, description="Подзаголовок категории. Обязательное поле.")
    budget = fields.Nested(CategoryBudgetSchema, required=True)
    rate = fields.Nested(CategoryRateSchema, required=True)
    audience = fields.Nested(CategoryAudienceSchema, required=True)
    rule = fields.Nested(CategoryRuleSchema, required=True)
    history = fields.List(
        fields.Nested(CategoryHistoryItemSchema),
        required=True,
        description="История изменений категории. Обязательное поле.",
    )


class CategoryListResponseSchema(Schema):
    items = fields.List(
        fields.Nested(CategoryListItemSchema),
        required=True,
        description="Список категорий. Обязательное поле.",
    )
    total = fields.Int(required=True, description="Общее количество категорий (для пагинации). Обязательное поле.")


class CategoryCreateSchema(Schema):
    category_id = fields.Str(
        required=False,
        allow_none=True,
        description="Идентификатор категории (UUID). Опционально — при отсутствии сгенерируется автоматически.",
    )
    name = fields.Str(required=True, description="Название категории. Обязательное поле.")
    subtitle = fields.Str(required=True, description="Подзаголовок категории. Обязательное поле.")
    budget_amount = fields.Float(
        required=True,
        description="Бюджет на одного пользователя по категории за период (ставка вычисляется автоматически). Обязательное поле.",
    )
    audience_segments = fields.List(
        fields.Str(),
        required=True,
        description="Сегменты аудитории категории. Обязательное поле.",
    )
    rule_id = fields.Str(required=True, description="Идентификатор правила отбора (возраст, пол, заработок). Обязательное поле.")


class CategoryUpdateSchema(Schema):
    name = fields.Str(required=False, description="Новое название категории. Опционально.")
    subtitle = fields.Str(required=False, description="Новый подзаголовок категории. Опционально.")
    budget_amount = fields.Float(
        required=False,
        description="Новый бюджет на одного пользователя по категории за период. Опционально.",
    )
    audience_segments = fields.List(
        fields.Str(),
        required=False,
        description="Новый список сегментов аудитории. Опционально.",
    )
    rule_id = fields.Str(required=False, description="Идентификатор правила отбора. Опционально.")


class RuleDetailSchema(Schema):
    rule_id = fields.Str(required=True, description="Идентификатор правила. Обязательное поле.")
    min_age = fields.Int(allow_none=True, description="Минимальный возраст. Опционально.")
    max_age = fields.Int(allow_none=True, description="Максимальный возраст. Опционально.")
    gender = fields.Str(allow_none=True, description="Пол. Опционально.")
    income = fields.Int(allow_none=True, description="Заработок. Опционально.")


class RuleListItemSchema(Schema):
    rule_id = fields.Str(required=True, description="Идентификатор правила. Обязательное поле.")
    min_age = fields.Int(allow_none=True, description="Минимальный возраст. Опционально.")
    max_age = fields.Int(allow_none=True, description="Максимальный возраст. Опционально.")
    gender = fields.Str(allow_none=True, description="Пол. Опционально.")
    income = fields.Int(allow_none=True, description="Заработок. Опционально.")


class RuleListResponseSchema(Schema):
    items = fields.List(
        fields.Nested(RuleListItemSchema),
        required=True,
        description="Список правил. Обязательное поле.",
    )
    total = fields.Int(required=True, description="Общее количество. Обязательное поле.")


class UserExistsResponseSchema(Schema):
    user_id = fields.Int(required=True, description="ID пользователя (BIGINT). Обязательное поле.")
    exists = fields.Bool(required=True, description="True, если пользователь есть в таблице users. Обязательное поле.")


class AdminRegisterSchema(Schema):
    login = fields.Str(required=True, description="Логин администратора. Обязательное поле.")
    password = fields.Str(required=True, description="Пароль администратора. Обязательное поле.")


class AdminLoginSchema(Schema):
    login = fields.Str(required=True, description="Логин администратора. Обязательное поле.")
    password = fields.Str(required=True, description="Пароль администратора. Обязательное поле.")


class AdminApproveSchema(Schema):
    admin_id = fields.Int(
        required=True,
        description="ID обычного администратора, которого нужно одобрить. Обязательное поле. В заголовке: Authorization: Bearer <токен супер-админа>.",
    )


class AdminAuthResponseSchema(Schema):
    admin_id = fields.Int(required=True, description="ID администратора. Обязательное поле.")
    login = fields.Str(required=True, description="Логин администратора. Обязательное поле.")
    main_admin = fields.Bool(required=True, description="Является ли администратор главным. Обязательное поле.")
    approved = fields.Bool(required=True, description="Одобрен ли администратор главным админом. Обязательное поле.")


class RuleCreateSchema(Schema):
    rule_id = fields.Str(
        required=False,
        description="Идентификатор правила. Опционально — сгенерируется автоматически.",
    )
    min_age = fields.Int(
        required=False,
        allow_none=True,
        description="Минимальный возраст. Опционально.",
    )
    max_age = fields.Int(
        required=False,
        allow_none=True,
        description="Максимальный возраст. Опционально.",
    )
    gender = fields.Str(
        required=False,
        allow_none=True,
        description="Пол. Опционально.",
    )
    income = fields.Int(
        required=False,
        allow_none=True,
        description="Заработок. Опционально.",
    )


class RuleUpdateSchema(Schema):
    min_age = fields.Int(
        required=False,
        allow_none=True,
        description="Минимальный возраст. Опционально.",
    )
    max_age = fields.Int(
        required=False,
        allow_none=True,
        description="Максимальный возраст. Опционально.",
    )
    gender = fields.Str(
        required=False,
        allow_none=True,
        description="Пол. Опционально.",
    )
    income = fields.Int(
        required=False,
        allow_none=True,
        description="Заработок. Опционально.",
    )


class AuditEventSchema(Schema):
    id = fields.Str(required=True, description="Идентификатор события аудита. Обязательное поле.")
    entity_type = fields.Str(required=True, description="Тип сущности. Обязательное поле.")
    entity_id = fields.Str(required=True, description="Идентификатор сущности. Обязательное поле.")
    action = fields.Str(required=True, description="Действие (create, update и т.д.). Обязательное поле.")
    actor = fields.Str(required=True, description="Кто выполнил действие. Обязательное поле.")
    created_at = fields.Str(required=True, description="Дата и время события в ISO 8601. Обязательное поле.")


class AuditListResponseSchema(Schema):
    items = fields.List(
        fields.Nested(AuditEventSchema),
        required=True,
        description="Список событий аудита. Обязательное поле.",
    )
    total = fields.Int(required=True, description="Количество событий в ответе. Обязательное поле.")


class UserSchema(Schema):
    id = fields.Int(required=True, description="ID пользователя (BIGINT). Обязательное поле.")
    name = fields.Str(required=True, description="Имя пользователя. Обязательное поле.")


class UserListResponseSchema(Schema):
    items = fields.List(
        fields.Nested(UserSchema),
        required=True,
        description="Список пользователей. Обязательное поле.",
    )
    total = fields.Int(required=True, description="Количество. Обязательное поле.")


class CalculateRequestSchema(Schema):
    user_id = fields.Int(
        required=True,
        description="ID пользователя (BIGINT, выбор на фронте). Обязательное поле.",
    )


class CalculateCategoryItemSchema(Schema):
    selection_id = fields.Str(
        required=False,
        allow_none=True,
        description="Идентификатор выбора (если уже сохранён) или null. Опционально.",
    )
    category_id = fields.Str(required=True, description="Идентификатор категории. Обязательное поле.")
    name = fields.Str(required=True, description="Название категории. Обязательное поле.")
    subtitle = fields.Str(required=True, description="Подзаголовок категории. Обязательное поле.")
    rate = fields.Nested(CategoryRateSchema, required=True)
    expected_benefit_amount = fields.Float(
        required=False,
        allow_none=True,
        description="Ожидаемая выгода по категории (null если ещё не выбран). Опционально.",
    )
    availability_status = fields.Str(
        required=False,
        allow_none=True,
        description="Статус доступности: available, budget_limited и т.д. Опционально.",
    )
    availability_reason = fields.Str(
        required=False,
        allow_none=True,
        description="Пояснение, если категория ограничена или недоступна. Опционально.",
    )


class CalculateResponseSchema(Schema):
    user_id = fields.Int(
        required=True,
        description="ID пользователя (BIGINT), для которого рассчитано. Обязательное поле.",
    )
    items = fields.List(
        fields.Nested(CalculateCategoryItemSchema),
        required=True,
        description="Категории/выборы для пользователя за период. Обязательное поле.",
    )


class SelectionDetailSchema(Schema):
    selection_id = fields.Str(required=True, description="Идентификатор выбора. Обязательное поле.")
    category_id = fields.Str(required=True, description="Идентификатор категории. Обязательное поле.")
    name = fields.Str(required=True, description="Название категории. Обязательное поле.")
    subtitle = fields.Str(required=True, description="Подзаголовок категории. Обязательное поле.")
    rate = fields.Nested(CategoryRateSchema, required=True)
    expected_benefit_amount = fields.Float(
        required=True,
        description="Ожидаемая выгода пользователя по выбранной категории. Обязательное поле.",
    )
    budget_message = fields.Str(
        required=False,
        allow_none=True,
        description="Сообщение о бюджетных ограничениях, если они есть. Опционально.",
    )


class SelectionDetailListResponseSchema(Schema):
    selection_id = fields.Str(
        required=True,
        description="Идентификатор запроса (ключ идемпотентности из path). Обязательное поле.",
    )
    items = fields.List(
        fields.Nested(SelectionDetailSchema),
        required=True,
        description="Список выбранных категорий по этому запросу. Обязательное поле.",
    )


class SelectionConfirmSchema(Schema):
    confirm = fields.Bool(
        required=False,
        missing=True,
        description="Флаг подтверждения выбора. Опционально, по умолчанию true.",
    )


class SelectionSubmitBodySchema(Schema):
    user_id = fields.Int(
        required=True,
        description="ID пользователя (BIGINT). Обязательное поле.",
    )
    category_ids = fields.List(
        fields.Str(),
        required=True,
        description="Ровно 5 идентификаторов категорий (UUID). Обязательное поле.",
    )


class SelectionSubmitResponseSchema(Schema):
    user_id = fields.Int(required=True, description="ID пользователя (BIGINT). Обязательное поле.")
    category_ids = fields.List(
        fields.Str(),
        required=True,
        description="Сохранённые 5 категорий. Обязательное поле.",
    )
    selection_ids = fields.List(
        fields.Str(),
        required=True,
        description="Созданные selection_id для каждой из 5 строк. Обязательное поле.",
    )
    message = fields.Str(required=True, description="Подтверждение сохранения. Обязательное поле.")


class SelectionConfirmResponseSchema(Schema):
    selection_id = fields.Str(required=True, description="Идентификатор подтверждённого выбора. Обязательное поле.")
    category_id = fields.Str(required=True, description="Идентификатор выбранной категории. Обязательное поле.")
    expected_benefit_amount = fields.Float(
        required=True,
        description="Ожидаемая выгода после подтверждения выбора. Обязательное поле.",
    )
    message = fields.Str(required=True, description="Комментарий backend по результату подтверждения. Обязательное поле.")


class ProgressItemSchema(Schema):
    selection_id = fields.Str(description="Идентификатор выбора. Опционально.")
    category_id = fields.Str(description="Идентификатор категории. Опционально.")
    status = fields.Str(description="Статус прогресса. Опционально.")


class ProgressListResponseSchema(Schema):
    items = fields.List(
        fields.Nested(ProgressItemSchema),
        required=True,
        description="Список записей прогресса. Обязательное поле.",
    )
    total = fields.Int(required=True, description="Общее количество. Обязательное поле.")

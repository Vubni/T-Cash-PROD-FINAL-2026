from marshmallow import Schema, fields, validate

class TokenResponseSchema(Schema):
    token = fields.Str(description="JWT-токен для авторизованных запросов. Передавать в заголовке Authorization: Bearer <token>.")

class UserAuthSchema(Schema):
    identifier = fields.Str(required=True, description="Логин или email пользователя — по нему ищется аккаунт при входе.")
    password = fields.Str(required=True, description="Пароль пользователя для проверки при входе.")
    
class UserProfileSchema(Schema):
    login = fields.Str(description="Уникальный логин пользователя (до 20 символов).")
    email = fields.Str(description="Email пользователя (до 256 символов).")
    name = fields.Str(description="Имя пользователя.")
    surname = fields.Str(description="Фамилия пользователя.")
    class_number = fields.Int(description="Номер класса (1–11).")
    class_letter = fields.Str(description="Буква класса (например, «А», «Б»).")
    telegram_name = fields.Str(description="Имя пользователя в Telegram после привязки аккаунта.")
    
class LoginEditSchema(Schema):
    login = fields.Str(required=True, description="Новый логин пользователя. Уникальный, до 20 символов. По нему пользователь будет входить.")
    
class EmailEditSchema(Schema):
    email = fields.Str(required=True, description="Новый email пользователя. До 256 символов. После смены может потребоваться верификация.")
    
class PasswordEditSchema(Schema):
    current_password = fields.Str(required=True, description="Текущий пароль пользователя (для проверки при смене).")
    new_password = fields.Str(required=True, description="Новый пароль. Должен соответствовать политике безопасности.")
    
class TelegramConnectSchema(Schema):
    url = fields.Str(required=True, description="Ссылка для привязки аккаунта Telegram.")
    
class EmailVerifyConfirmSchema(Schema):
    token = fields.Str(required=True, description="Токен подтверждения email из письма или ссылки верификации.")
    

class ScheduleGetSchema(Schema):
    date = fields.Date(required=True, description="Дата, на которую запрашивается расписание (формат YYYY-MM-DD).")
    
class ClubsListSchema(Schema):
    type = fields.Str(required=False, missing="my", description="Тип списка: 'my' — клубы пользователя, иначе — общий список. По умолчанию my.")
    offset = fields.Int(required=False, missing=0, description="Смещение для пагинации: сколько записей пропустить. По умолчанию 0.")
    limit = fields.Int(required=False, missing=100, description="Максимум записей в ответе. По умолчанию 100.")
    
class ClubGetSchema(Schema):
    club_id = fields.Int(required=True, description="ID клуба (число). Передаётся в path при запросе одного клуба.")
    
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
    id = fields.Int(description="ID направления/министерства (используется при создании клуба как administration).")
    title = fields.Str(description="Название направления (например, министерство образования).")

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
    title = fields.Str(description="Название достижения для отображения.")
    description = fields.Str(description="Текстовое описание достижения.")
    xp = fields.Str(description="Текущий набранный опыт пользователя по этому достижению (строка для гибкости формата).")
    need_xp = fields.Str(description="Порог опыта, необходимый для получения достижения (строка). Сравнивать с xp для прогресс-бара.")

class TeachersSchema(Schema):
    name = fields.Str(description="ФИО учителя для отображения в расписании.")
    subject = fields.Str(description="Название предмета, который ведёт этот учитель.")

class AchievementsSchema(Schema):
    title = fields.Str(description="Название достижения или новости.")
    description = fields.Str(description="Описание достижения/новости.")
    image_path = fields.Str(description="Относительный путь к картинке достижения; склеивать с base URL медиа при отображении.")
    date = fields.Date(description="Дата события или публикации (YYYY-MM-DD).")
    url = fields.Str(description="Ссылка на полную новость или материал; открывать по клику.")

class TelegramAuthSchema(Schema):
    url = fields.Str(description="Ссылка на Telegram-бота для привязки аккаунта; перенаправлять пользователя по этой ссылке.")
    token = fields.Str(description="Токен для опроса статуса: прошла ли авторизация в боте (использовать в последующих запросах проверки).")

class ForgotPasswordSchema(Schema):
    identifier = fields.Str(required=True, description="Логин или email пользователя — по нему ищется аккаунт для отправки письма сброса пароля.")
    new_password = fields.Str(required=True, description="Новый пароль, который пользователь хочет установить после перехода по ссылке из письма.")

class ForgotPasswordConfirmSchema(Schema):
    confirm = fields.Int(required=True, description="Код подтверждения сброса пароля (из письма или ссылки).")


    
class ErrorDetailSchema(Schema):
    name = fields.Str(description="Имя параметра или поля, из-за которого вернулась ошибка (для привязки к форме на фронте).")
    type = fields.Str(description="Тип ошибки валидации: например missing — поле обязательно, value_error — неверный формат.")
    message = fields.Str(description="Человекочитаемое сообщение об ошибке; показывать пользователю под полем.")
    value = fields.Raw(description="Значение, которое было передано (если было); может быть null.", allow_none=True)


class FieldErrorItemSchema(Schema):
    field = fields.Str(description="Имя поля в теле запроса, по которому ошибка валидации.")
    issue = fields.Str(description="Описание проблемы (например, «must be non-negative», «invalid UUID»). Показывать под полем.")
    rejectedValue = fields.Raw(allow_none=True, description="Значение, которое отклонил сервер; может быть null. Полезно для отладки и подсказок.")


class HttpErrorSchema(Schema):
    code = fields.Str(description="Строковый код ошибки: UNAUTHORIZED (401), FORBIDDEN (403), NOT_FOUND (404), VALIDATION_ERROR (422) и т.д. Использовать для ветвления логики на фронте.")
    message = fields.Str(description="Краткое сообщение об ошибке для пользователя или логов.")
    traceId = fields.Str(description="Уникальный идентификатор запроса; передавать в поддержку при обращении по ошибке.")
    timestamp = fields.Str(description="Время ответа в формате ISO 8601.")
    path = fields.Str(description="URL path запроса, который вернул ошибку.")
    details = fields.Dict(allow_none=True, description="Дополнительные данные (объект); зависит от эндпоинта, может быть null.")
    fieldErrors = fields.List(
        fields.Nested(FieldErrorItemSchema),
        allow_none=True,
        description="При 422 — список ошибок по полям (field, issue, rejectedValue). Показывать под соответствующими полями формы. Иначе null.",
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
    error = fields.Str(description="Общее сообщение об ошибке запроса; показывать вверху формы или в тосте.")
    errors = fields.List(fields.Nested(ErrorDetailSchema), description="Список ошибок по полям: name, type, message, value — для привязки к полям формы.")
    received_params = fields.Dict(description="Параметры запроса, которые сервер принял; полезно для отладки при частичной валидации.")


class AlreadyBeenTaken(Schema):
    name = fields.Str(description="Имя поля (например login или email), значение которого уже занято другим пользователем.")
    error = fields.Str(description="Сообщение вида «уже занято»; показывать под полем при регистрации/редактировании.")


class CategoryBudgetSchema(Schema):
    amount = fields.Float(
        required=True,
        description="Бюджет на одного пользователя по категории за период (в рублях). Обязательное поле.",
    )


class CategoryRateSchema(Schema):
    min = fields.Float(required=True, description="Минимальная ставка кэшбэка в процентах (0–100). Показывается пользователю как нижняя граница диапазона. Обязательное поле.")
    max = fields.Float(required=True, description="Максимальная ставка кэшбэка в процентах (0–100). Показывается пользователю как верхняя граница диапазона. Обязательное поле.")


GENDER_ENUM = ["male", "female", "other"]
NAME_SUBTITLE_MAX = 500

class CategoryRuleSchema(Schema):
    rule_id = fields.Str(required=True, description="UUID правила отбора. Связь категории с правилом (возраст, пол, доход). Обязательное поле.")
    min_age = fields.Int(allow_none=True, description="Минимальный возраст пользователя в годах; null — ограничение не задано. Используется для отбора по правилу.")
    max_age = fields.Int(allow_none=True, description="Максимальный возраст пользователя в годах; null — ограничение не задано. Используется для отбора по правилу.")
    gender = fields.Str(allow_none=True, validate=validate.OneOf(GENDER_ENUM), description="Пол пользователя: male, female или other; null — ограничение не задано.")
    income = fields.Int(allow_none=True, description="Доход пользователя (в рублях); null — ограничение не задано. Используется для отбора по правилу.")


class CategoryHistoryItemSchema(Schema):
    changed_at = fields.Str(required=True, description="Дата и время изменения в ISO 8601. Обязательное поле.")
    changed_by = fields.Str(required=True, description="Идентификатор или логин того, кто внёс изменение (для аудита). Обязательное поле.")
    field = fields.Str(required=True, description="Имя поля, которое изменили (name, budget_amount и т.д.). Обязательное поле.")
    old_value = fields.Raw(required=False, allow_none=True, description="Значение до изменения; может быть null для сложных типов. Опционально.")
    new_value = fields.Raw(required=False, allow_none=True, description="Значение после изменения; может быть null для сложных типов. Опционально.")


class CategoryListItemSchema(Schema):
    id = fields.Str(required=True, description="UUID категории. Используется в path и в запросах выбора. Обязательное поле.")
    name = fields.Str(required=True, description="Название категории для отображения (до 500 символов). Обязательное поле.")
    subtitle = fields.Str(required=True, description="Краткий подзаголовок/описание категории для карточки (до 500 символов). Обязательное поле.")
    budget = fields.Nested(CategoryBudgetSchema, required=True, description="Бюджет по категории: amount — сумма на одного пользователя за период (руб).")
    rate = fields.Nested(CategoryRateSchema, required=True, description="Диапазон ставок кэшбэка: min и max в процентах для отображения пользователю.")


class CategoryDetailSchema(Schema):
    id = fields.Str(required=True, description="UUID категории. Обязательное поле.")
    name = fields.Str(required=True, description="Название категории. Обязательное поле.")
    subtitle = fields.Str(required=True, description="Подзаголовок категории. Обязательное поле.")
    budget = fields.Nested(CategoryBudgetSchema, required=True, description="Бюджет: amount — бюджет на одного пользователя за период (руб).")
    rate = fields.Nested(CategoryRateSchema, required=True, description="Диапазон ставок кэшбэка: min, max в процентах.")
    rule = fields.Nested(CategoryRuleSchema, required=True, description="Правило отбора: rule_id, min_age, max_age, gender, income — условия показа категории пользователю.")
    history = fields.List(
        fields.Nested(CategoryHistoryItemSchema),
        required=True,
        description="История изменений категории (кто, когда, какое поле, старое/новое значение). Для аудита в админке. Обязательное поле.",
    )


class CategoryListResponseSchema(Schema):
    items = fields.List(
        fields.Nested(CategoryListItemSchema),
        required=True,
        description="Массив категорий по текущей странице (с учётом offset/limit). Обязательное поле.",
    )
    total = fields.Int(required=True, description="Общее число категорий в системе; нужно для пагинации (например, «показано 10 из total»). Обязательное поле.")


class CategoryCreateSchema(Schema):
    category_id = fields.Str(
        required=False,
        allow_none=True,
        description="UUID категории. Не передавайте — сервер сгенерирует сам. Нужен только если фронт хочет задать свой ID. Опционально.",
    )
    name = fields.Str(required=True, validate=validate.Length(min=1, max=NAME_SUBTITLE_MAX), description="Название категории для отображения пользователю (1–500 символов). Обязательное поле.")
    subtitle = fields.Str(required=True, validate=validate.Length(min=1, max=NAME_SUBTITLE_MAX), description="Подзаголовок/краткое описание категории (1–500 символов). Обязательное поле.")
    budget_amount = fields.Float(
        required=True,
        description="Бюджет на одного пользователя по категории за период, в рублях. Не может быть отрицательным. Обязательное поле.",
    )
    rate_min = fields.Int(required=True, description="Минимальный кэшбек в процентах (0–100). Обязательное поле.")
    rate_max = fields.Int(required=True, description="Максимальный кэшбек в процентах (0–100). Обязательное поле.")
    # rule_id не передаётся при создании — правило создаётся отдельно и привязывается к категории через PATCH категории или эндпоинт правил.


class CategoryUpdateSchema(Schema):
    name = fields.Str(required=False, validate=validate.Length(min=1, max=NAME_SUBTITLE_MAX), description="Новое название категории (1–500 символов). Опционально.")
    subtitle = fields.Str(required=False, validate=validate.Length(min=1, max=NAME_SUBTITLE_MAX), description="Новый подзаголовок категории (1–500 символов). Опционально.")
    budget_amount = fields.Float(
        required=False,
        description="Новый бюджет на одного пользователя за период (руб). Не может быть отрицательным. Опционально.",
    )
    rate_min = fields.Int(required=False, description="Новый минимальный кэшбек в процентах (0–100). Опционально.")
    rate_max = fields.Int(required=False, description="Новый максимальный кэшбек в процентах (0–100). Опционально.")
    rule_id = fields.Str(required=False, description="UUID правила отбора. Привязывает категорию к правилу (возраст, пол, доход) или меняет привязку. Опционально.")


class RuleDetailSchema(Schema):
    rule_id = fields.Str(required=True, description="UUID правила. Используется при привязке к категории (rule_id в PATCH категории). Обязательное поле.")
    min_age = fields.Int(allow_none=True, description="Минимальный возраст пользователя в годах; null — ограничение не задано.")
    max_age = fields.Int(allow_none=True, description="Максимальный возраст пользователя в годах; null — ограничение не задано.")
    gender = fields.Str(allow_none=True, validate=validate.OneOf(GENDER_ENUM), description="Пол: male, female или other; null — без ограничения.")
    income = fields.Int(allow_none=True, description="Доход в рублях; null — без ограничения. Используется для отбора по правилу.")


class RuleListItemSchema(Schema):
    rule_id = fields.Str(required=True, description="UUID правила. Обязательное поле.")
    min_age = fields.Int(allow_none=True, description="Минимальный возраст (годы); null — не задано.")
    max_age = fields.Int(allow_none=True, description="Максимальный возраст (годы); null — не задано.")
    gender = fields.Str(allow_none=True, validate=validate.OneOf(GENDER_ENUM), description="Пол: male, female или other; null — не задано.")
    income = fields.Int(allow_none=True, description="Доход (руб); null — не задано.")


class RuleListResponseSchema(Schema):
    items = fields.List(
        fields.Nested(RuleListItemSchema),
        required=True,
        description="Массив правил по текущей странице (offset/limit). Обязательное поле.",
    )
    total = fields.Int(required=True, description="Общее число правил; для пагинации. Обязательное поле.")


class UserExistsResponseSchema(Schema):
    user_id = fields.Str(required=True, description="UUID пользователя, по которому проверяли наличие. Обязательное поле.")
    exists = fields.Bool(required=True, description="true — пользователь есть в системе (можно использовать для расчёта/выбора); false — нет. Обязательное поле.")


ADMIN_LOGIN_MAX = 255
ADMIN_PASSWORD_MAX = 255

class AdminRegisterSchema(Schema):
    login = fields.Str(required=True, validate=validate.Length(min=1, max=ADMIN_LOGIN_MAX), description="Логин нового администратора (1–255 символов). Уникальный. Обязательное поле.")
    password = fields.Str(required=True, validate=validate.Length(min=1, max=ADMIN_PASSWORD_MAX), description="Пароль администратора (1–255 символов). После регистрации нужна одобрение главным админом. Обязательное поле.")


class AdminLoginSchema(Schema):
    login = fields.Str(required=True, validate=validate.Length(min=1, max=ADMIN_LOGIN_MAX), description="Логин администратора (1–255 символов). Обязательное поле.")
    password = fields.Str(required=True, validate=validate.Length(min=1, max=ADMIN_PASSWORD_MAX), description="Пароль администратора (1–255 символов). Обязательное поле.")


class AdminApproveSchema(Schema):
    admin_id = fields.Int(
        required=True,
        description="ID заявки администратора (из списка pending), которого одобряет главный админ. В заголовке нужен Bearer-токен супер-админа. Обязательное поле.",
    )


class PendingAdminItemSchema(Schema):
    admin_id = fields.Int(required=True, description="ID заявки на роль админа; передавать в approve для одобрения.")
    login = fields.Str(required=True, description="Логин заявителя (для отображения в списке заявок).")


class PendingAdminsResponseSchema(Schema):
    items = fields.List(
        fields.Nested(PendingAdminItemSchema),
        required=True,
        description="Список заявок на администратора, ещё не одобренных главным админом (approved = false).",
    )


class AdminAuthResponseSchema(Schema):
    admin_id = fields.Int(required=True, description="ID администратора в системе. Обязательное поле.")
    login = fields.Str(required=True, description="Логин администратора. Обязательное поле.")
    main_admin = fields.Bool(required=True, description="true — главный/супер-админ (может одобрять других); false — обычный админ. Обязательное поле.")
    approved = fields.Bool(required=True, description="true — админ одобрен и может работать; false — ожидает одобрения главным админом. Обязательное поле.")
    token = fields.Str(required=True, description="JWT для запросов в админ-API. Передавать в заголовке Authorization: Bearer <token>. Обязательное поле.")


class RuleCreateSchema(Schema):
    rule_id = fields.Str(
        required=False,
        description="UUID правила. Не передавайте — сервер сгенерирует. Нужен только если фронт задаёт свой ID. Опционально.",
    )
    min_age = fields.Int(
        required=False,
        allow_none=True,
        description="Минимальный возраст в годах; null — ограничение не задано. Используется при привязке правила к категории.",
    )
    max_age = fields.Int(
        required=False,
        allow_none=True,
        description="Максимальный возраст в годах; null — не задано. Опционально.",
    )
    gender = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(GENDER_ENUM),
        description="Пол: male, female или other; null — не задано. Опционально.",
    )
    income = fields.Int(
        required=False,
        allow_none=True,
        description="Доход в рублях; null — не задано. Опционально.",
    )


class RuleUpdateSchema(Schema):
    min_age = fields.Int(
        required=False,
        allow_none=True,
        description="Новый минимальный возраст (годы); null — снять ограничение. Опционально.",
    )
    max_age = fields.Int(
        required=False,
        allow_none=True,
        description="Новый максимальный возраст (годы); null — снять ограничение. Опционально.",
    )
    gender = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(GENDER_ENUM),
        description="Пол: male, female или other; null — снять ограничение. Опционально.",
    )
    income = fields.Int(
        required=False,
        allow_none=True,
        description="Новый доход (руб); null — снять ограничение. Опционально.",
    )


AUDIT_ENTITY_TYPE_MAX = 50
AUDIT_ENTITY_ID_MAX = 64
AUDIT_ACTION_MAX = 50
AUDIT_ACTOR_MAX = 255

class AuditEventSchema(Schema):
    id = fields.Str(required=True, description="Уникальный идентификатор события аудита. Обязательное поле.")
    entity_type = fields.Str(required=True, validate=validate.Length(min=1, max=AUDIT_ENTITY_TYPE_MAX), description="Тип сущности (1–50 символов): category, rule, admin, client. Обязательное поле.")
    entity_id = fields.Str(required=True, validate=validate.Length(min=1, max=AUDIT_ENTITY_ID_MAX), description="ID сущности (1–64 символа). Обязательное поле.")
    action = fields.Str(required=True, validate=validate.Length(min=1, max=AUDIT_ACTION_MAX), description="Тип действия (1–50 символов): create, update, delete, selection. Обязательное поле.")
    actor = fields.Str(required=True, validate=validate.Length(min=1, max=AUDIT_ACTOR_MAX), description="Кто выполнил действие (1–255 символов): логин или ID. Обязательное поле.")
    created_at = fields.Str(required=True, description="Дата и время события в ISO 8601. Обязательное поле.")


class AuditListResponseSchema(Schema):
    items = fields.List(
        fields.Nested(AuditEventSchema),
        required=True,
        description="Список событий аудита по текущей странице. Обязательное поле.",
    )
    total = fields.Int(required=True, description="Общее количество событий (для пагинации). Обязательное поле.")


class UserSchema(Schema):
    id = fields.Int(required=True, description="Внутренний ID пользователя (BIGINT). Для отображения в админке. Обязательное поле.")
    name = fields.Str(required=True, description="Имя пользователя (для отображения в списках). Обязательное поле.")


class UserListResponseSchema(Schema):
    items = fields.List(
        fields.Nested(UserSchema),
        required=True,
        description="Список пользователей по текущей странице (offset/limit). Обязательное поле.",
    )
    total = fields.Int(required=True, description="Общее количество пользователей; для пагинации. Обязательное поле.")


class CalculateRequestSchema(Schema):
    user_id = fields.Str(
        required=True,
        description="UUID пользователя, для которого нужно рассчитать доступные категории и выгоду. Берётся с фронта (текущий пользователь). Обязательное поле.",
    )


class CalculateCategoryItemSchema(Schema):
    selection_id = fields.Str(
        required=False,
        allow_none=True,
        description="UUID сохранённого выбора по этой категории; null — пользователь ещё не выбрал эту категорию. Нужен для подтверждения выбора и отображения «уже выбрано».",
    )
    category_id = fields.Str(required=True, description="UUID категории. Используется при отправке выбора (category_ids) и в эндпоинтах выбора. Обязательное поле.")
    name = fields.Str(required=True, description="Название категории для отображения. Обязательное поле.")
    subtitle = fields.Str(required=True, description="Подзаголовок категории для карточки. Обязательное поле.")
    rate = fields.Nested(CategoryRateSchema, required=True, description="Диапазон ставок кэшбэка (min, max в %).")
    expected_benefit_amount = fields.Float(
        required=False,
        allow_none=True,
        description="Ожидаемая сумма выгоды в рублях по этой категории за период. null — категория ещё не выбрана или выгода не рассчитана. Показывать пользователю как «до X ₽».",
    )
    availability_status = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(["available", "budget_limited", "unavailable"]),
        description="Код доступности: available — можно выбрать, budget_limited — лимит бюджета исчерпан, unavailable — недоступно.",
    )
    availability_reason = fields.Str(
        required=False,
        allow_none=True,
        description="Человекочитаемое пояснение, почему категория недоступна или ограничена (например, «бюджет исчерпан»). Показывать под карточкой при status != available.",
    )


class CalculateResponseSchema(Schema):
    user_id = fields.Str(
        required=True,
        description="UUID пользователя, для которого выполнен расчёт. Совпадает с user_id из тела запроса. Обязательное поле.",
    )
    items = fields.List(
        fields.Nested(CalculateCategoryItemSchema),
        required=True,
        description="Список категорий с расчётом выгоды и доступности для данного пользователя. Отображать как карточки выбора. Обязательное поле.",
    )
    already_selected_categories = fields.Bool(
        required=True,
        description="true — данные взяты из кэша (уже выбранные пользователем категории из selections); false — категории рассчитаны заново (через ML).",
    )


class SelectionDetailSchema(Schema):
    selection_id = fields.Str(required=True, description="UUID сохранённого выбора. Используется в эндпоинтах подтверждения и в расчёте. Обязательное поле.")
    category_id = fields.Str(required=True, description="UUID выбранной категории. Обязательное поле.")
    name = fields.Str(required=True, description="Название категории для отображения. Обязательное поле.")
    subtitle = fields.Str(required=True, description="Подзаголовок категории. Обязательное поле.")
    rate = fields.Nested(CategoryRateSchema, required=True, description="Диапазон ставок кэшбэка (min, max в %).")
    expected_benefit_amount = fields.Float(
        required=True,
        description="Ожидаемая выгода в рублях по этой выбранной категории за период. Показывать пользователю. Обязательное поле.",
    )
    budget_message = fields.Str(
        required=False,
        allow_none=True,
        description="Текст о бюджетных ограничениях (например, «часть выгоды может быть ограничена бюджетом»). null — ограничений нет. Показывать под карточкой при необходимости.",
    )


class SelectionDetailListResponseSchema(Schema):
    selection_id = fields.Str(
        required=True,
        description="Идентификатор запроса выбора из path (идемпотентный ключ). Совпадает с тем, что передали в URL. Обязательное поле.",
    )
    items = fields.List(
        fields.Nested(SelectionDetailSchema),
        required=True,
        description="Список выбранных категорий по этому запросу (selection_id). Обязательное поле.",
    )


class SelectionConfirmSchema(Schema):
    confirm = fields.Bool(
        required=False,
        missing=True,
        description="true — подтвердить выбор категории; false — отменить. По умолчанию true. Опционально.",
    )


class SelectionCurrentResponseSchema(Schema):
    category_ids = fields.List(
        fields.Str(),
        required=True,
        description="Массив UUID выбранных категорий (только id, без лишних полей).",
    )


class SelectionSubmitBodySchema(Schema):
    user_id = fields.Str(
        required=True,
        description="UUID пользователя, который отправляет выбор. Обычно текущий пользователь с фронта. Обязательное поле.",
    )
    category_ids = fields.List(
        fields.Str(),
        required=True,
        description="Массив UUID категорий, которые пользователь выбрал. Количество должно совпадать с max_selection_count из настроек (например, ровно 5). Обязательное поле.",
    )


class SelectionSubmitResponseSchema(Schema):
    user_id = fields.Str(required=True, description="UUID пользователя, для которого сохранён выбор. Обязательное поле.")
    category_ids = fields.List(
        fields.Str(),
        required=True,
        description="Сохранённый список UUID выбранных категорий (только id, в том же порядке что в запросе).",
    )


class SelectionConfirmResponseSchema(Schema):
    selection_id = fields.Str(required=True, description="UUID подтверждённого выбора. Обязательное поле.")
    category_id = fields.Str(required=True, description="UUID категории, по которой подтверждён выбор. Обязательное поле.")
    expected_benefit_amount = fields.Float(
        required=True,
        description="Итоговая ожидаемая выгода в рублях после подтверждения. Показывать пользователю. Обязательное поле.",
    )
    message = fields.Str(required=True, description="Сообщение от бэкенда (успех или предупреждение). Показать пользователю. Обязательное поле.")


class CategorySelectionSettingsSchema(Schema):
    all_categories = fields.Int(
        required=False,
        description="0 — показывать пользователю только ограниченный набор категорий по max_selection_count; 1 — показывать все категории без ограничения по количеству выбора. Опционально.",
    )
    max_selection_count = fields.Int(
        required=False,
        description="Сколько категорий пользователь может выбрать за один период (например, 5). Используется при валидации category_ids в POST выбора. Опционально.",
    )


class CategorySelectionSettingsResponseSchema(Schema):
    all_categories = fields.Int(
        required=True,
        description="Текущее значение: 0 — ограниченный выбор, 1 — все категории. Нужно для отображения правил выбора на фронте. Обязательное поле.",
    )
    max_selection_count = fields.Int(
        required=True,
        description="Текущий лимит выбора категорий (например, 5). Фронт должен отправлять ровно столько category_ids. Обязательное поле.",
    )


class ProgressItemSchema(Schema):
    selection_id = fields.Str(description="UUID выбора; связь с записью выбора. Опционально.")
    category_id = fields.Str(description="UUID категории по этой записи. Опционально.")
    status = fields.Str(description="Статус обработки/прогресса по этой записи (например, pending, confirmed). Используйте для отображения прогресса. Опционально.")


class ProgressListResponseSchema(Schema):
    items = fields.List(
        fields.Nested(ProgressItemSchema),
        required=True,
        description="Список элементов прогресса по выборам/категориям. Обязательное поле.",
    )
    total = fields.Int(required=True, description="Общее количество записей; для пагинации. Обязательное поле.")

# Решения

Дата проектирования: 2026-10-19, Asia/Qyzylorda (UTC+05:00).
Статус будущих решений — предложено, реализация проверяется по этапам.

1. FastAPI + Pydantic: заданный стек, типизированные API и OpenAPI.
2. PostgreSQL: транзакции, ограничения, блокировки и реальные concurrency tests.
   SQLite не заменяет PostgreSQL для проверки конкурентного доступа.
3. uv: обязательное требование; uv.lock фиксируется, воспроизводимая установка
   через uv sync --locked. Исходная uv-заготовка перенесена в backend.
4. SQLAlchemy 2 async + asyncpg: согласованы с async FastAPI и будущим SSE.
   Новая операция получает своё соединение/сессию, не делит AsyncSession.
5. Modular monolith: отдельные API, настройки и будущие сервисы без микросервисов.
6. Liveness отдельно от readiness: живой HTTP-процесс может сообщить отказ БД.
   Readiness ограничен 5 секундами и возвращает безопасный 503.
7. Vite proxy: одинаковые /api URL для browser и Compose, без широкого CORS.
   Vite dev server только для локальной разработки; production hosting не включён.
8. SSE вместо WebSocket (план): серверные изменения однонаправленны; после
   reconnect клиент читает snapshot. HTTP используется для пользовательских действий.
9. Event row lock (план): проще для объяснения и проверки вместимости/FIFO,
   чем optimistic retry и сложные распределённые блокировки. Механизм обязателен
   для всех операций с количеством мест, включая редактирование вместимости.
10. Database outbox (план): надёжное сохранение задания в бизнес-транзакции,
    локальный worker без Redis/Celery. SMTP delivery остаётся at-least-once.
11. Mailpit: эмуляция SMTP и просмотр писем локально без внешних аккаунтов.
12. Миграции вместе с моделями в Phase 2: в Foundation таблиц нет, пустая
    миграция не нужна. Alembic уже в зависимостях.

## Phase 2 — 2026-10-20, Asia/Qyzylorda

13. Вместо локального аккаунта выбран один серверный bearer token организатора:
    минимальный доступ для задания без таблиц пользователей/ролей. Случайный
    секрет генерируется в игнорируемый .env, проверяется constant-time сравнением.
    Пустой секрет отключает запись, короткий отклоняется конфигурацией.
    Токен в UI хранится в памяти, без localStorage/sessionStorage. Для удалённого
    размещения потребуется HTTPS; сейчас опубликованы только loopback-порты.
14. Event имеет UTC timestamp, UUID и schedule_version. Модель/миграция задают
    CHECK для положительной вместимости и непустого названия. Schema валидирует
    timezone и будущую дату; PATCH отличает пропуск поля от null.
15. PATCH/DELETE используют row lock, чтобы последовательно менять Event.
    Для одновременного редактирования одного поля действует last-write-wins;
    это не optimistic version control. Версия расписания нужна будущим заданиям,
    а не заменяет блокировки регистрации в Phase 3.
16. Миграции проверяются upgrade/downgrade/upgrade в UUID-схемах PostgreSQL.
    Fixture удаляет только созданную ею схему и не очищает таблицы приложения.
    Alembic check проверяет отсутствие расхождений metadata и миграции.
17. Для совместной работы Windows/WSL используется отдельная .venv-windows;
    исходная .venv имела Linux-конфигурацию и вызвала ошибку при Windows uv sync.
    Для восстановления Linux-окружения используйте uv sync в WSL.
    Новых зависимостей не добавлено.
18. Demo seed имеет стабильные UUID и INSERT ON CONFLICT DO NOTHING: повторный
    запуск не перезаписывает изменения организатора.

Дополнительные официальные источники Phase 2:
- https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic
- https://docs.pydantic.dev/latest/api/standard_library_types/#datetimes

## Phase 3 — 2026-10-22, Asia/Qyzylorda

19. Registration получает статус confirmed/waiting/cancelled вместо отдельной
    WaitingList. Монотонный номер на Event задаёт FIFO без неоднозначных timestamp.
    Rejoin сохраняет строку, но выдаёт новый номер в конце очереди.
20. Один Event row lock сериализует все API изменения мест и очереди. DB-trigger
    поддерживает confirmed_count, CHECK запрещает overselling. Одного CHECK с
    SELECT count(*) по другой таблице PostgreSQL не поддерживает; trigger и
    счётчик дают транзакционную проверку при прямом DML регистраций.
21. Клиент создаёт 256-bit ключ до POST: тот же ключ обеспечивает безопасный
    retry, не раскрывая существующий доступ по одному email. Сервер хранит hash.
    Потеря доступа пока не восстанавливается; email verification появится только
    при отдельной реализации и сейчас не заявляется.
22. Новая регистрация/отмена/rejoin после старта запрещены. Повтор отмены уже
    отменённой записи не имеет эффекта. Увеличение capacity продвигает FIFO;
    удаление события с историей и снижение capacity ниже занятых мест дают 409.
23. Статус с queue_position формируется одной SQL snapshot-операцией, чтобы
    чтение не смешивало состояние до и после продвижения. Список организатора
    использует тот же запрос, без N+1 подсчётов по сети.
24. Добавлен email-validator (через uv, 41 package в lock) для EmailStr;
    нормализация case-insensitive в пределах event, с DB UNIQUE и CHECK.
25. Phase 3 использует polling 10 секунд. Это промежуточный способ отображения
    изменений, не объявляется выполнением запланированного SSE в Phase 5.

Официальные источники Phase 3:
- https://www.postgresql.org/docs/17/ddl-constraints.html
- https://www.postgresql.org/docs/16/trigger-definition.html
- https://docs.pydantic.dev/latest/api/networks/#emailstr

Официальные источники, просмотренные в этой сессии:
- https://docs.astral.sh/uv/guides/integration/docker/
- https://docs.astral.sh/uv/concepts/projects/sync/
- https://vite.dev/guide/
- https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html

## Phase 4 — 2026-10-24, Asia/Qyzylorda

26. Ticket хранит случайный 128-bit код, UNIQUE(code), частичный UNIQUE для
    активного билета регистрации, checked_in_at и revoked_at. Код отделён от
    ключа управления участника: билет не даёт права отмены регистрации.
27. Выдача и отзыв входят в транзакцию регистрации/продвижения. Rejoin после
    отмены выдаёт новый билет при получении места. Миграция backfill создаёт
    билеты только confirmed-записям.
28. Check-in блокирует Event в том же порядке, что отмена. Повтор возвращает
    прежний timestamp и already_checked_in=true. После входа отмена запрещена,
    чтобы использованное место не передавалось очереди. До/после starts_at вход
    разрешён; отдельного временного окна в задании нет.
29. Посещаемость считается по активным использованным билетам, без второго
    изменяемого счётчика. Verify читает snapshot и не резервирует право входа:
    check-in повторно проверяет действительность под блокировкой.

## Phase 5 — 2026-10-24, Asia/Qyzylorda

30. PostgreSQL Notification outbox, отдельный процесс app.worker из того же
    образа backend. Уникальные логические ключи, retry/backoff и lease заменяют
    потерянные in-memory background tasks. Новых runtime dependencies нет:
    SMTP через smtplib в asyncio.to_thread, Mailpit из существующего Compose.
31. Claim берёт Event, затем Notification с SKIP LOCKED; SMTP идёт после commit.
    Ack сравнивает lease_token. Это не блокирует регистрацию на время SMTP.
    Нельзя одновременно гарантировать отсутствие уже передаваемого старого
    письма и атомарность с внешним SMTP; проверяем актуальность на claim и
    документируем возможный дубль/письмо в полёте. Exactly-once delivery не заявлена.
32. Reminder: один на регистрацию и версию расписания, даже при rejoin.
    Менее 24 часов — немедленно; после начала — skip. При переносе новая версия
    получает своё напоминание, старые задания проверяют версию. Waiting получают
    перенос; cancelled исключены. Подтверждение/продвижение — один раз на билет.
33. SSE + транзакционные Event.revision: проверка версий раз в секунду на поток.
    Для задания проще воспроизводимого LISTEN reconnect lifecycle и работает
    с несколькими API-процессами. Это DB polling внутри SSE, не native PG push.
    Нет replay промежуточных состояний: каждый reconnect вызывает snapshot API.
    Цена чтения версий и широкая invalidation приемлемы для локального приложения;
    LISTEN/NOTIFY или общий broadcaster — возможная оптимизация позже.
34. Реальный browser shutdown выявил незакрываемый Vite proxy SSE. Добавлено
    завершение downstream при upstream close, именованный heartbeat (10 секунд)
    и клиентский watchdog (25 секунд). Резервный polling сохраняется.

Просмотренные официальные источники:
- https://www.postgresql.org/docs/18/sql-select.html (SKIP LOCKED и очереди)
- https://www.starlette.io/requests/ (disconnect streaming requests)

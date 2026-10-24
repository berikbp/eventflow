# Архитектура

## Реализовано в Phase 1–5

Модульный монолит FastAPI и отдельное React SPA.
Browser → Vite /api proxy → FastAPI → SQLAlchemy AsyncEngine → PostgreSQL.
В Compose приложения обращаются по service DNS; браузер знает только localhost.
Настройки backend читаются из корневого .env или окружения.
Engine создаётся в lifespan и закрывается при shutdown. /health проверяет процесс,
/health/ready выполняет SELECT 1 с лимитом времени и отвечает 503 при сбое БД.
Публичные health ответы не содержат строку подключения.

PostgreSQL хранится в именованном volume. Mailpit принимает SMTP от отдельного outbox-worker.
Реализована модель Event и миграция 0001_events. API разделён на routes, schemas,
services и models. SQLAlchemy AsyncSession создаётся на запрос; транзакциями записи
управляет сервис, update/delete блокируют строку события. Схема создаётся только
миграциями, а не create_all при старте приложения.

Контейнер выполняет Alembic upgrade head и затем запускает Uvicorn через exec.
Это запуск одного экземпляра; при масштабировании миграции нужно вынести в
отдельный deploy step. Локальный запуск вне Docker требует ручного upgrade head.

Публичны GET /events и /events/{id}. Создание, PATCH и DELETE требуют серверный
ORGANIZER_TOKEN из .env, минимум 32 символа. При пустом токене запись отключена.
GET /organizer/session проверяет доступ. Один общий организатор управляет всеми
событиями; учётных записей и сессий в БД нет. Секрет не попадает в frontend build,
хранится только в памяти вкладки и передаётся в Authorization header.

Новые даты должны быть timezone-aware и будущими, нормализуются в UTC. PATCH
сохраняет пропущенные поля и не принимает null/пустой объект. Изменение starts_at
увеличивает schedule_version; повтор одинаковой даты не увеличивает версию.
DELETE запрещён при наличии истории регистраций. Capacity нельзя снизить ниже
confirmed_count; увеличение вместимости продвигает ожидающих в той же транзакции.

## Registration и транзакции — Phase 3

Registration: UUID, event_id, нормализованный email, SHA-256 token_hash, status,
queue_order, created_at/updated_at. UNIQUE для (event,email), (event,token_hash)
и (event,queue_order). Event получил confirmed_count и next_registration_order.
Миграция 0002 создаёт таблицу, CHECK/FK/индексы и trigger учёта мест.

Порядок записи: Event FOR UPDATE → проверка idempotency/доступа → выделение
очереди/смена статуса → flush → FIFO promotion → commit. Все API изменения
мест, включая capacity, используют одну блокировку. Триггер Registration меняет
счётчик Event; CHECK 0 <= confirmed_count <= capacity обеспечивает целостность
при INSERT/UPDATE/DELETE регистраций. Вручную счётчик не обновляется сервисами.
Это защита для поддерживаемых записей и обычного DML, не от вмешательства DBA.
Используется стандартный PostgreSQL READ COMMITTED.

Секрет управления генерируется браузером через crypto.getRandomValues(32 bytes),
передаётся при создании как X-Registration-Token, при чтении/отмене как Bearer.
Он одновременно обеспечивает авторизацию и идемпотентный retry: знание email
не даёт право получить ID/ключ существующей записи. В БД только SHA-256.
После успеха UI показывает ссылку /registrations/{id}#token=... . Fragment не
попадает на сервер, Referrer-Policy задан как no-referrer в HTML. Pending attempt
сохраняется в sessionStorage вкладки до ответа; успешная личная ссылка — в URL,
пользователь сохраняет её самостоятельно. Потерянный ключ пока не восстанавливается.

Статус и queue_position читаются одним SQL snapshot. Организаторский список
не раскрывает token_hash. Приватные API-ответы имеют Cache-Control: no-store.
UI получает SSE invalidation и повторно читает API. Polling 10 секунд — резерв.

Cancelled — сохраняемая запись: retry create не возобновляет её. Явный rejoin
выдаёт новый queue_order, без второго ряда на тот же email. После starts_at
участие менять нельзя. Повтор отмены cancelled и повтор create существующей
авторизованной записи остаются безопасными чтениями без нового эффекта.

## Уведомления и real-time — Phase 5

- Event уже реализован: UUID, дата UTC, вместимость, версия расписания и timestamps.
- Registration реализована в Phase 3, включая FIFO, доступ и concurrency tests.
- Ticket реализован в Phase 4: уникальный код, registration_id, checked_in_at, отзыв.
- Notification: вид, ссылки на Event/Registration/Ticket, версия расписания,
  deduplication_key UNIQUE, due_at/available_at, attempts, lease, sent/skipped.

API routes → схемы → бизнес-сервисы → SQLAlchemy. Repository вводить только
при повторяющейся логике доступа. Background worker — отдельный процесс того же
backend; PostgreSQL outbox исключает необходимость Redis/Celery.

Любая операция, меняющая занятость/очередь, блокирует Event через SELECT FOR UPDATE
в общей транзакции. Под той же блокировкой проверяются повторная регистрация,
вместимость, отмена и FIFO-продвижение. Билет создаётся в этой транзакции; outbox также создаётся в этой транзакции.
Все пути изменения соблюдают один порядок блокировок; проверено в Phase 3.
Порядок FIFO задаётся монотонным ключом при получении блокировки, а не только
timestamp с возможными совпадениями.

SSE /updates передаёт только invalidate с fingerprint версий событий. Триггеры
Event/Registration/Ticket изменяют Event.revision в бизнес-транзакции. Сервер
раз в секунду читает версии, не удерживая соединение между проверками. Изменение
starts_at > now тоже входит в fingerprint, чтобы закрытие регистрации обновляло UI.
Начальный snapshot отправляется всегда, Last-Event-ID не служит журналом replay.
После reconnect клиент перечитывает актуальные API; пропущенные промежуточные
состояния не воспроизводятся. Это согласованное состояние, а не аудит событий.
Подходит для небольшого локального приложения, цена — O(число событий) чтения на
подписчика в секунду. Для масштаба возможен LISTEN/NOTIFY с общей подпиской.
Heartbeat каждые 10 секунд, watchdog 25 секунд, ошибки БД закрывают поток.
Vite proxy явно завершает клиентский SSE при закрытии upstream.

Outbox хранит логическое задание, тело письма формируется из актуальных данных
при захвате. Сервис создаёт задания в транзакции выдачи билета/переноса. Worker:
неблокирующий поиск кандидата → Event FOR UPDATE SKIP LOCKED → Notification
FOR UPDATE SKIP LOCKED → проверка статуса/билета/версии → lease/commit → SMTP
в отдельном thread → условный ack по lease_token. SMTP не удерживает DB locks.
Отказ сохраняет класс ошибки и backoff; перезапуск восстанавливает processing
после lease_until. Один занятый Event может отложить следующую попытку до нового
цикла; это локальный worker, не система с гарантией большой пропускной способности.
Тело письма и ключ управления не хранятся в outbox. Код билета берётся из Ticket.
Логи ошибок не печатают адреса, коды и SMTP response.

UNIQUE ключи: confirmation/promotion на ticket.id, reminder/rescheduled на
registration.id + schedule_version. Reminder для confirmed: за 24 часа, либо
сразу, если осталось меньше суток; после начала пропускается. Перенос создаёт
новую версию уведомления/напоминания, старые не проходят проверку на claim.
Cancelled пропускаются, waiting получают перенос, но не reminder или билет.
Rejoin может восстановить пропущенный reminder, но не отправленный той же версии.
Worker idempotent INSERT SELECT восстанавливает отсутствующие reminders для
старых confirmed после миграции; старые confirmation ретроспективно не рассылает.

Гарантия UNIQUE относится к логическим заданиям. SMTP доставка at-least-once:
сбой после передачи письма до ack может дать повтор с тем же Message-ID.
Уже захваченное/передаваемое письмо нельзя атомарно отменить вместе с изменением
PostgreSQL. Актуальность определяется на claim; следующий rescheduled сообщает
новую дату. Это явное ограничение границы PostgreSQL/внешнего SMTP.

Организатор: общий bearer token (Phase 2). Участник: личный bearer token и SHA-256
в БД (Phase 3); email сам по себе не даёт право отмены. Полной системы ролей нет.

## Tickets — Phase 4

Миграция 0003 создаёт Ticket и backfill confirmed-регистраций. Один активный
билет на регистрацию защищён частичным UNIQUE индексом. Отзыв сохраняет историю.
Выдача при регистрации/FIFO/capacity promotion и отзыв при отмене атомарны.
Check-in использует Event FOR UPDATE; повтор не меняет checked_in_at.
CHECK запрещает одновременно отозванный и использованный билет. API отмены
отклоняет уже использованный билет. Организаторский verify не меняет состояние.
Ticket API и персональные ответы имеют no-store. UI показывает билет только
через ключ управления, проверка/вход доступны через токен организатора.

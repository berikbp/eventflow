# Журнал разработки

## 2026-10-19 — Phase 1, Asia/Qyzylorda (UTC+05:00)

Временные точки получены командой Get-Date -Format o во время сессии.
Инструмент: Codex / GPT-6 family; точный вариант модели не предоставлен средой.

### 14:23:34 +05:00 — анализ и выбор структуры

Исходное состояние: uv-заготовка без зависимостей, пустой README, src/eventflow
с Hello World, локальная .venv; Git без коммитов и без настроенной identity.
AGENTS.md в проекте и проверенных родительских каталогах не обнаружены.
Запрос прочитан целиком в UTF-8; первая попытка чтения показала неверную кодировку.
Предложены отдельные backend/frontend, modular monolith, async SQLAlchemy,
PostgreSQL, Vite proxy и health/readiness. Работа ограничена Phase 1.

Существующий pyproject и Python pin перенесены в backend, авторские метаданные
сохранены. uv init сообщил, что проект уже инициализирован; использована имеющаяся
заготовка. Примерный CLI Hello World удалён как заменённый FastAPI-приложением.

### 14:27:59 +05:00 — первоначальная реализация и проверки

Добавлены FastAPI app factory/lifespan, настройки из .env, SQLAlchemy async engine,
/health и /health/ready с SELECT 1, timeout и безопасным 503. Добавлены тесты.
Frontend создан create-vite 9.3.0 react-ts; подключены Router, Query, Tailwind.
Страница показывает pending/error/success, обновляет readiness и позволяет retry.
Созданы Dockerfile, Compose, PostgreSQL volume, Mailpit, .env.example и .gitignore.

Первый pytest: 3 passed, 1 skipped (TEST_DATABASE_URL ещё не задан).
Первый ruff check/format обнаружил длинную строку в PostgreSQL test; исправлено.
Frontend npm run build и npm run lint прошли; npm install сообщил 0 vulnerabilities.
Docker daemon сначала был недоступен; docker desktop start успешно его запустил.
Начата загрузка образов и первая сборка.

Исходный промпт скопирован без изменения; SHA-256 обоих файлов совпал:
86AAD66C115D744658664D2DDC73C50DBEF4E5C2D9844F3DC540777A35331014.

### 14:30:24–14:31:13 +05:00 — документация и исправления инструментов

Созданы requirements checklist, architecture, decisions, testing, agent-prompts,
README с PowerShell-командами. Будущие Event/Registration/Ticket/Outbox и механизмы
блокировок/SSE описаны как планы, а не готовые функции.

Первый TestClient дал deprecation warning о Starlette/httpx. Тесты переведены
на httpx AsyncClient + ASGITransport с явным lifespan: 3 passed, 1 skipped,
без этого warning. Ruff format --check аварийно завершился на BOM в записанном
PowerShell файле; тестовые файлы нормализованы в UTF-8 без BOM, LF. Затем
ruff check и format --check прошли, uv lock --check прошёл (39 packages).

Навык computer-use прочитан для планируемой проверки UI. Browser tool вернул
No browser is available; визуальная проверка не выполнена, не заявляется пройденной.
Проверено исключение .env, обеих .venv, node_modules и dist через git check-ignore.

### 14:31:36–14:32:21 +05:00 — реальный запуск

Пользователь предоставил Git identity berikbp / beriktarakov7@gmail.com;
применено через git config --local. Глобальная конфигурация не менялась.

Оба Dockerfile успешно собраны. Первый Compose up остановился на занятом порту
5432; чужой процесс не трогали. Внешний порт БД изменён на 5433 в Compose,
.env.example, локальном .env и README. Внутренний порт остался 5432.

Повторный docker compose up --build -d --wait прошёл. Новый именованный
eventflow_postgres_data создан при первом запуске. Запущены все четыре сервиса.
Это первый запуск в данном окружении, не проверка на другой чистой машине.

С TEST_DATABASE_URL на реальный контейнер PostgreSQL: **4 passed in 0.95s**.
uv run ruff check .: passed; uv run ruff format --check .: 8 files formatted;
uv lock --check: passed. HTTP-проверки:
- GET :8000/health → 200, status ok.
- GET :8000/health/ready → 200, status ok, database ok.
- GET :5173/api/health/ready → 200, status ok, database ok.
- GET :5173 → 200; GET :8025 → 200.

### 14:32:59 +05:00 — проверка отказа и восстановления

docker compose stop db: readiness вернул 503, liveness оставался 200.
docker compose up -d --wait db восстановил БД; readiness снова вернул ok.
После docker compose restart backend и docker compose up -d --wait сервисы
снова запустились. PostgreSQL volume не удалялся. Доменная сохранность данных
пока не тестируется: схемы мероприятий ещё нет.

Повторные frontend npm run build и npm run lint прошли после удаления шаблонных
неиспользуемых картинок и CSS. TypeScript build включён в npm run build.

Осталось за пределами Phase 1: модели и Alembic migrations, доступ, мероприятия,
регистрация/очередь, concurrency tests, билеты, SSE, outbox/worker, письма,
reminders, demo data и полноценная проверка двух вкладок. Следующий этап — Phase 2.
Визуальный browser QA остаётся ручной проверкой из-за недоступности браузера.

### Завершение и Git

После перечисленных проверок созданы отдельные коммиты backend и frontend:
- 856906f — chore: initialize FastAPI backend with uv and health checks.
- b1d4aa5 — feat: add React foundation page with API readiness status.

Compose, README и документация фиксируются следующим отдельным коммитом.
Даты коммитов не переопределялись; автор настроен локально по ответу пользователя.
Добавлен .gitattributes: исходники LF, исходный промпт сохраняется побайтно.
Последняя HTTP-проверка после restart backend: frontend proxy readiness — ok.
Контрольная системная отметка после двух коммитов: 2026-10-19T14:34:01+05:00.
При staged diff --check оригинальный CRLF-промпт сначала дал замечания о CR;
для архивного файла задан whitespace=cr-at-eol без изменения его байтов.

## 2026-10-19T14:46:06–14:47:21+05:00 — исправление readiness UI

Пользователь сообщил об ошибке `["readiness"] data is undefined` на странице.
Причина: checkHealth возвращала Promise<void>; успешный HTTP-ответ не давал
данных TanStack Query. Первоначальная сборка и HTTP smoke checks этого не выявили.

Функция вынесена в frontend/src/api/health.ts, возвращает типизированный
проверенный объект readiness. Добавлены три regression tests через встроенный
Node test runner: успех через настоящий QueryClient, HTTP 503 и неверный JSON.
Обновлены README и testing.md с командой npm test. Инструмент: Codex / GPT-6 family.

npm test: 3 passed. Первая локальная сборка/lint не запустились из-за отсутствия
tsc/oxlint в node_modules; npm ci --include=dev восстановил зависимости,
после чего npm run build и npm run lint прошли. Docker Compose frontend
пересобран и перезапущен через up -d --build --wait frontend, успешно.
Живая проверка checkHealth через QueryClient и :5173/api/health/ready вернула
{status: ok, database: ok}, состояние query — success. Первый inline Node smoke
command не выполнился из-за PowerShell quoting; повтор через stdin прошёл.
git diff --check прошёл. Визуальный browser QA не выполнялся.

## 2026-10-20 — Phase 2: Database & Event Management

Часовой пояс Asia/Qyzylorda (UTC+05:00). Системные отметки ниже получены Get-Date.
Инструмент: Codex / GPT-6 family, точный вариант не доступен. Субагентов не было.
Промпт пользователя сохранён в prompts/002-phase-2.txt.

### 15:35:01 +05:00 — осмотр и план

Рабочее дерево чистое, четыре контейнера Phase 1 работали. AGENTS.md в проекте
не найден. Изучены текущие конфигурация, API, frontend, README и архитектура.
План: Event, миграция Alembic, публичный read API, защищённый CRUD организатора,
список/детали и формы UI, PostgreSQL integration tests. Регистрация и уведомления
исключены из объёма текущего этапа.

### Реализация до контрольной отметки 15:56:11 +05:00

Добавлены UUID Event, title/description, starts_at timestamptz, capacity,
schedule_version, created_at/updated_at. CHECK ограничения и индекс starts_at/id.
Alembic async environment и 0001_events; контейнер мигрирует БД перед Uvicorn.
Сервисы отделены от endpoints, AsyncSession на запрос, транзакции записи и
row lock для PATCH/DELETE. Реализованы пагинация, 404, строгие схемы/422,
UTC-нормализация и инкремент версии при переносе.

Выбран общий bearer token организатора вместо аккаунтов: защищает все записи,
не требуется для чтения; пустой токен отключает запись, минимум 32 символа.
Новый setup_local добавляет случайный секрет в игнорируемый .env без вывода
секрета в терминал, сохраняет существующие настройки и непустой токен.

Первый Windows uv run обнаружил Linux .venv и попытался пересоздать её, но
остановился на lib64 reparse point с Access denied. Дальнейшие команды выполнены
с UV_PROJECT_ENVIRONMENT=.venv-windows, оно исключено из Git/Docker context.
При возврате к WSL Linux-окружение можно восстановить uv sync. Зависимости и
lockfiles не менялись. Первые замечания Ruff исправлены форматированием/import
sorting; Alembic path_separator=os убрал deprecation warning.

Первые PostgreSQL API tests: 27 passed. Каждому тесту выделяется отдельная схема
test_events_<uuid>; миграции применяются туда программно. Teardown удаляет только
свою схему. Проверяется CRUD, доступ, пагинация, ошибки, DB CHECK, schedule_version,
upgrade/downgrade/upgrade и drift check. Дополнительно протестированы безопасное
отключение записи, короткий токен, идемпотентный setup и demo seed.

Frontend: публичный список/детали, отдельный маршрут /system для readiness,
доступ организатора, формы создания/PATCH и подтверждение удаления. Токен
находится в памяти вкладки. Добавлены состояния загрузки/ошибки/пустого списка,
успешные сообщения, invalidation Query cache и локальная дата ↔ UTC.
Сборка прошла; замечание lint о Date при рендере карточки устранено.

### 15:58:02–15:58:41 +05:00 — запуск и persistence

setup_local создал ORGANIZER_TOKEN только в .env. Alembic upgrade head применён
к локальной БД, current = 0001_events. Alembic check: no new upgrade operations.
Compose build/up --wait успешно обновил приложения. Seed создан и запущен дважды:
две demo-записи со стабильными UUID, без перезаписи существующих данных.

Живой smoke через :5173/api: неавторизованный доступ = 401, правильный token
проверен, временное событие создано (201), прочитано и изменено (200), удалено
(204), последующий GET = 404. Временная запись убрана в finally.
После docker compose restart db backend и up --wait demo Event с UUID
00000000-0000-4000-8000-000000000001 по-прежнему читается, capacity=30.

### 16:00:44–16:01:15 +05:00 — финальная проверка

- uv run pytest -q с TEST_DATABASE_URL: **31 passed in 3.66s**, без warnings.
- uv run ruff check .: passed; format --check: 28 файлов отформатированы.
- uv lock --check: passed, 39 packages.
- uv run alembic check: no new upgrade operations detected.
- npm test: **7 passed**; npm run build и npm run lint прошли без замечаний.
- docker compose config --quiet и build/up --wait прошли.
- git check-ignore подтвердил исключение .env и .venv-windows.
- Живой TypeScript API + QueryClient загрузил список и детали через frontend
  proxy, оба запроса success. Контейнерный alembic check также прошёл.
- Повторный контейнерный seed не изменил существующие demo-записи.

Browser inventory = apps: [], browsers: []; визуальный QA и ручной сценарий
кликами не выполнялись. Это остаётся ограничением проверки. Обновлены README,
архитектура, решения, требования и testing.md. После проверок изменения
фиксируются отдельными коммитами backend, frontend и документации с реальными
датами и ранее согласованной Git identity.

Следующий этап: Registration и FIFO waiting list, ограничения email, транзакции
последнего места, отмена/продвижение и concurrency tests PostgreSQL.
До появления регистраций следует дополнить правила DELETE и уменьшения capacity.
SSE, outbox, письма и последствия переноса для уведомлений ещё не реализованы.

## 2026-10-22 — Phase 3: Registration & Waiting List

Timezone Asia/Qyzylorda (UTC+05:00). Временные отметки получены Get-Date во время
работы. Инструмент Codex / GPT-6 family; точный вариант модели не предоставлен.
Субагентов не было. Реальный запрос: prompts/003-phase-3.txt.

### 16:23:24 +05:00 — анализ

Рабочее дерево чистое, Phase 2 контейнеры работают. AGENTS.md в проекте не найден.
Прочитаны Event/model/schema/service, app factory, PostgreSQL fixtures и UI.
План: Registration, FIFO, idempotency, личный ключ, cancellation/promotion,
защита capacity/delete и PostgreSQL concurrency tests. Tickets и outbox оставлены
для следующих этапов. Просмотрены официальные PostgreSQL/Pydantic docs.

### 16:27:12–16:27:43 +05:00 — модель и базовые concurrency tests

Добавлена миграция 0002_registrations: Registration с CHECK/FK/UNIQUE, индекс FIFO;
Event получил confirmed_count и next_registration_order. DB-trigger меняет
counter в той же транзакции, CHECK отклоняет переполнение. Все API операции
мест используют Event FOR UPDATE. Отмена вызывает FIFO-продвижение, rejoin
возвращает запись в конец. Редактирование capacity соблюдает count и продвигает
очередь; удаление события с любой историей запрещено.

Email валидируется EmailStr, strip/lower и DB UNIQUE. Через uv добавлен
email-validator с dnspython; lock содержит 41 package. Клиентский 256-bit ключ
служит credential и idempotency key; сервер хранит только SHA-256. Другой ключ
на тот же email даёт 409 без получения чужого ID или данных управления.
Участник читает/отменяет по Bearer; список с email доступен только организатору.

Существующие 31 тест прошли после добавления модели. Fixtures перенесены в
conftest.py для повторного использования. Следующий прогон: 43 passed in 10.51s,
включая последнее место и 20/5, retries, отмены, FIFO, raw DB guard/rollback.
Замечания Ruff по длинным строкам исправлены форматированием и разбиением SQL.

### 16:29:07–16:31:25 +05:00 — UI и расширенная регрессия

Добавлены форма регистрации на странице события, личный статус/cancel/rejoin,
ссылка с fragment-секретом, private API clients и список участников организатора.
UI опрашивает данные каждые 10 секунд. Pending attempt в sessionStorage переживает
reload, очищается после успешного ответа; при отключённом storage retry остаётся
в памяти. Добавлен no-referrer, private API responses no-store.

В ходе review статус и queue_position переведены на один SQL snapshot: иначе
чтение могло смешать статус до promotion и позицию после него. Список использует
тот же запрос без сетевого N+1. После изменения 43 backend tests снова прошли.

Расширены тесты гонок capacity/cancel vs registration и прямых конкурентных
INSERT, DB email uniqueness и reuse ключа на другой email.
Итоговый pytest: **49 passed in 13.75s**. Frontend: **12 passed**, TypeScript/Vite
build и lint прошли. Новые frontend tests проверяют secret headers, link fragment,
retry/pending recovery и protected list. Визуальный browser QA не выполнен:
inventory вернул apps=[] и browsers=[].

Alembic check перед применением новой миграции к public БД сообщил Target database
is not up to date. Это было состояние Phase 2 public schema, не расхождение
применённой модели: integration tests уже проверяли head в изолированных схемах.
После старта обновлённого контейнера миграция применена, current показывает
0002_registrations (head), check: No new upgrade operations detected.

### 16:34:04–16:35:41 +05:00 — Compose, живой smoke и persistence

docker compose up --build -d --wait прошёл. Сборка загрузила обновлённые Python/Node
base images и зависимости; загрузка uv runtime packages заняла около 2m20s.
Новый backend стартовал с миграцией; все сервисы доступны.

Живой smoke через frontend proxy создал отдельное событие на 1 место и двух
участников, проверил confirmed/waiting, отмену → promotion, rejoin, private read,
organizer list, no-store и запрет удаления истории. Все проверки прошли.
Временные ключи не выводились, хранились только в игнорируемом локальном файле.

После restart PostgreSQL/backend личный доступ и состояния (первый waiting,
второй confirmed) сохранились. Затем в транзакции с Event lock удалены только
созданные smoke-регистрации и их событие; проверено обнуление trigger counter.
Файл с временными ключами удалён. Demo/user events не затронуты.

Финальные проверки: Alembic check passed; Ruff check passed; format --check —
36 files formatted; uv lock --check passed, 41 packages. README, architecture,
decisions, checklist, testing и prompts обновлены с фактическим состоянием.
После проверок создаются отдельные backend/frontend/docs коммиты с ранее
согласованной Git identity и настоящими датами.

Ограничения: нет Ticket/check-in, email/outbox, SSE; используется polling.
Владение email не проверяется, восстановление потерянного личного ключа пока
не реализовано. UI тестировался сборкой/модулями и живыми API, без browser clicks.
Следующий этап — Phase 4: билеты и одноразовый check-in.

## 2026-10-24 — Phase 4, продолжение незавершённой работы

Время записей: Asia/Qyzylorda, UTC+05:00. Контрольные системные отметки текущей
сессии: 20:49:52 (анализ), 21:18:42 (окружение), 21:20:33 (проверки),
21:31:04 (перезапуск), 21:37:19 (финальная запись). Это реальные отметки команд,
а не попытка восстановить время предыдущего агента.
Инструмент: Codex, GPT-6 по данным среды; точный вариант неизвестен.
Субагенты не использовались.

Исходное состояние: HEAD 2719c62, Phase 3. Найдены незакоммиченные изменения
предыдущего агента: Ticket, миграция 0003, сервисы/API и test_tickets.py.
Они проверены и продолжены; не выдаются за код, целиком созданный в этой сессии.
Изучены исходники backend/frontend, миграции, тесты, документация и последние
коммиты. Phase 1 повторно не создавалась: исходный мастер-промпт прочитан вместе
с актуальным контекстом незавершённой Phase 4.

Реализовано и проверено:
- Выдача билета при confirmed и FIFO/capacity promotion в бизнес-транзакции.
- Отзыв при отмене, новый код после повторного получения места, backfill.
- Organizer verify и check-in под Event lock, идемпотентный повтор с прежним
  timestamp. После входа отмена запрещена; счётчик посещаемости вычисляется.
- Личный экран билета, отдельная форма проверки/подтверждения входа,
  attendance в панели и отметки в списке участников. Остаётся polling 10 секунд.
- Дополнены frontend API tests; исправлена длинная SQL-строка теста для Ruff.

Проблемы окружения и фактические результаты:
- Первая uv sync не смогла разрешить DNS в sandbox; эскалация была прервана
  пользователем. После возобновления загрузка в /tmp cache шла медленно и была
  остановлена. Offline sync из стандартного cache обнаружила недостающий
  dnspython. Обычная uv sync --locked с сетевым доступом успешно установила
  зависимости. Один pytest запущен до окончания установки и завершился ошибкой
  импорта pygments; после установки повторный запуск успешен.
- npm test первоначально прошёл, build не нашёл Linux TypeScript package
  в node_modules от другого окружения. npm ci --cache /tmp/eventflow-npm-cache
  восстановил зависимости без изменения lock-файла.
- TEST_DATABASE_URL=... .venv/bin/python -m pytest -q: **59 passed in 24.08s**,
  настоящая PostgreSQL, отдельные UUID-схемы. В том числе 20 конкурентных
  check-in дают один новый вход, гонка cancel/check-in, отзыв, rejoin, backfill,
  rollback, UNIQUE и регрессия Phase 1–3.
- Ruff check: passed; format --check: 42 files already formatted.
  uv lock --check --offline: passed, 41 packages.
- npm test: все 4 файла passed. Отдельный запуск Node с --test-isolation=none
  показал **14 passed**. npm run build и npm run lint: passed.
- docker compose up --build -d --wait: passed, все сервисы запущены. Backend
  зависимости скачивались 2m50s. alembic check в контейнере: No new upgrade
  operations detected.
- Живой smoke через http://127.0.0.1:5173/api: отдельное событие, два участника,
  билет/отсутствие билета у waiting, отмена, продвижение, отзыв старого кода,
  вход, повтор, attendance=1 — passed.
- docker compose restart db backend и up -d --wait: passed. После restart
  билет и checked_in_at совпали с сохранёнными, повтор вернул already_checked_in.
  Затем удалены только smoke-регистрации/событие под Event lock с проверкой
  UUID и названия. Временный файл с ключами удалён скриптом; user/demo не менялись.
- git diff --check: passed. Созданы a4cb808 (backend), e30a102 (frontend).

README, architecture, decisions, requirements, testing и реальные выдержки
промптов обновлены. Три файла docs/prompts пользователь намеренно удалил во
время работы и явно попросил не фиксировать удаления: они остаются вне коммитов.
Предыдущие тексты доступны в истории Git, ссылки в docs указывают на неё.
Git sandbox имел read-only .git: коммиты выполнены после разрешённой эскалации.

Ограничения: browser visual/E2E не выполнены — доступного browser tool нет.
SSE, transactional outbox и email пока не реализованы. Следующий этап — Phase 5.

## 2026-10-24 — Phase 5: real-time и устойчивые уведомления

Часовой пояс Asia/Qyzylorda, UTC+05:00. Системные контрольные отметки:
21:39:04 (анализ), 21:45:01 (проверки), 21:48:33 (browser smoke),
21:53:58 (проверка исправления SSE), 21:59:32 (очистка), 22:00:41 (финальный audit).
Время предыдущих записей не переписывалось. Инструмент Codex, GPT-6 по данным
среды; точный вариант модели не указан. Субагенты не использовались.

Пользователь: «ok let's continue our next phase». HEAD на старте 5c26bf0,
Phase 4 работала; в рабочем дереве только три намеренных удаления docs/prompts,
которые пользователь ранее просил не коммитить. Сохранено это ограничение.

План и решения:
- Notification outbox в PostgreSQL, миграция 0004 вместе с Event.revision и
  транзакционными триггерами Event/Registration/Ticket для SSE invalidation.
- Бизнес-транзакция создаёт confirmation/promotion вместе с Ticket, перенос
  создаёт rescheduled и reminder текущей версии. UNIQUE logical key.
- Отдельный app.worker, без новых dependencies: smtplib через to_thread.
  Claim: Event → Notification SKIP LOCKED → lease/commit, SMTP без DB locks,
  ack только для того же lease_token. Retry/backoff, recovery expired leases.
- Reminder один на регистрацию/версию, менее суток — сразу, после старта skip.
  Rejoin не повторяет sent reminder той же версии. При переносе новая версия
  получает своё напоминание. Worker backfill покрывает старые confirmed.
- SSE /updates отправляет только сигнал без private data. Сервер читает версии
  событий раз в секунду; начальный snapshot есть на каждом reconnect. Нет replay
  промежуточных событий. Для локального задания выбран этот простой механизм;
  его нагрузка и возможная оптимизация LISTEN/NOTIFY описаны в architecture.
- Exactly-once SMTP не заявляется. Уже захваченное письмо может уйти одновременно
  с переносом/отменой; актуальность проверена на claim, а не атомарно с SMTP.
  Сбой после отправки до ack может повторить доставку с тем же Message-ID.

Реализация:
- Добавлены Notification model/service/worker, migration 0004, Settings SMTP,
  worker в Compose и .env.example. Email содержит билет и public URL;
  ключ управления не сохраняется в outbox и остаётся в личной ссылке браузера.
- SSE endpoint, Event revision triggers, React EventSource + Query invalidation,
  статус соединения, heartbeat и watchdog. Polling 10 секунд оставлен резервом.
- UI больше не говорит, что email отсутствует; формы/дата/списки обновляются.
- Добавлены PostgreSQL tests уведомлений и SSE, frontend regression и live scripts.

Фактические проверки:
- Первоначальная регрессия после миграции: 59 passed in 20.87s.
- Первые notification tests: 11 passed in 8.99s.
- После добавления SSE: 73 passed in 34.39s.
- С rejoin/новой версией/переносом позже: **76 passed in 37.44s** PostgreSQL.
  Из них 14 новых outbox-сценариев и 3 SSE. Fixture UUID schemas сохраняет user DB.
- После изменения heartbeat повторены SSE: 3 passed in 2.07s.
- Frontend: 15 passed через Node --test-isolation=none, npm test (5 файлов),
  TypeScript/Vite build и lint прошли. Frontend test проверяет watchdog mock timers.
- Ruff check passed, format --check: 50 files formatted; uv lock --check прошёл,
  41 packages. lock/dependencies не менялись.
- Compose build/up прошёл, все пять сервисов работают. Миграция применена,
  Alembic check в контейнере: No new upgrade operations detected.

Browser QA и обнаруженная ошибка:
Локальный Chromium 153 был в кеше Playwright, но не запускался из-за недостающих
libnspr4/libnss3/libasound2t64. Три пакета скачаны/распакованы в /tmp без системной
установки. Запущен отдельный headless профиль, управление через CDP и Node WebSocket.
Первые попытки тестового скрипта выявили ожидание .ticket-code до завершения
загрузки и влияние оставленных вкладок на число соединений; исправлен сам runner.

Реальный shutdown обнаружил дефект приложения: Vite proxy оставлял downstream
SSE открытым после остановки backend, соединение визуально оставалось connected.
Добавлена передача upstream close через response.end, именованный heartbeat
10 секунд и watchdog 25 секунд. CDP offline сам по себе не оборвал существующий
поток, поэтому финальный reconnect проверен настоящей остановкой/start backend.

Полный двухвкладочный smoke прошёл: регистрация видна организатору за **953ms**,
waiting, cancellation → promotion, private ticket, verify, check-in, attendance=1,
повторная проверка билета, перенос, остановка API, reconnect обеих вкладок с новым
snapshot. Ассерты обновления ограничены 5 секундами, меньше fallback polling 10s.
Runtime JS exceptions не обнаружены. Снимок background tab ожидал активации;
после bringToFront сохранены /tmp/eventflow-phase5-dashboard.png и
/tmp/eventflow-phase5-mobile.png и визуально просмотрены. Панель 1440px и билет
390px читаемы, горизонтальное переполнение мобильной страницы не обнаружено.
Runner сохранён в frontend/scripts/smoke_phase5_browser.mjs с универсальными
путями, CDP timeout и bringToFront; Node syntax check и lint прошли.

Live SMTP/restart QA:
При остановленном worker scripts/smoke_phase5.py prepare создал отдельное событие
с уникальным email и **двумя pending** (confirmation + immediate reminder).
Перезапущены db/backend, запущен worker. verify проверил **два sent и два письма
в Mailpit** с кодами билетов. После дополнительного restart worker повтор verify
также показал два письма. Один ранний prepare попал в остановленный для browser
теста backend и получил 502; после восстановления повтор успешно завершён.
Удалены только собственные smoke events/registrations под Event lock с проверкой
UUID/названия, включая события неуспешных браузерных попыток. State-файлы удалены.
Синтетические email-письма сохранены в Mailpit для просмотра; user/demo не менялись.

Документация и воспроизводимые команды дополнены в README, architecture,
decisions, requirements, testing, agent-prompts. Основные ограничения теперь:
локальные общий organizer token/SMTP/Vite, нет email ownership verification и
восстановления утраченной личной ссылки; SSE читает DB версии, SMTP at-least-once.
Полная QA из чистой среды и финальная поставка остаются Phase 6.

После проверок созданы отдельные коммиты:
- 7224fb1 — outbox, worker, SSE, migration и backend/live tests.
- 1771a62 — frontend SSE/reconnect, proxy fix, watchdog и browser runner.
Коммиты сделаны с настоящими датами; удаления docs/prompts не включены.

## 2026-10-25 — Phase 6: стабилизация и техническая подготовка к сдаче

Часовой пояс Asia/Qyzylorda, UTC+05:00. Реальные контрольные отметки системных
команд: 15:56:59 (аудит), 16:07:21 (проверки), 16:10:21 (отчёт),
16:11:30 (UX), 16:14:26 (mobile), 16:15:09 (сборка), 16:17:03 (финальный audit).
Codex, семейство GPT-6 по данным среды, точный вариант неизвестен. Субагенты
не использовались. Пользователь: «ok let's continue our next phase».
HEAD на старте 33b3365; три удаления docs/prompts по-прежнему не коммитятся.

На запрос GitHub/эссе пользователь ответил: «пока я не создал гитхаб и не начал
эссе». Создан docs/submission.md с настоящим состоянием и двумя оставшимися
действиями кандидата. Remote отсутствует, репозиторий не публиковался, личное
эссе/обстоятельства не выдумывались. Техническая Phase 6 отделена от фактической
отправки задания.

Аудит выявил и исправил:
- Worker сначала выбирал event_id самого раннего задания, затем мог пропустить
  занятый Event и остановиться, хотя другая очередь готова. Теперь выбирает
  незаблокированный Event с готовыми jobs через FOR UPDATE SKIP LOCKED, сохраняя
  Event → Notification lock order. Regression-тест удерживает lock одного
  мероприятия и проверяет доставку для другого.
- Обычный /events при отказе PostgreSQL выдавал общий 500. Сетевые/операционные
  отказы session dependency преобразуются в безопасный 503 с Retry-After: 3 и
  no-store. Constraint/programming errors не маскируются. Readiness не изменён.
- Добавлен тест late SMTP failure после истечения lease: успешный ack нового
  владельца остаётся sent, запоздалый старый worker не переписывает результат.
- Check-in после отмены билета мог оставить прошлый «действителен» на экране.
  Ошибка admission очищает старый verify result; добавлены loading/error/retry
  на странице проверки, скрыты устаревшие публичные формы/данные при ошибке query.
- На 320px длинный title без пробелов переполнял check-in. Добавлен перенос
  текста main и перенос pagination/footer; пять узких страниц прошли повторно.

Backend verification:
Два новых regression-теста сначала реально упали: worker вернул None при
готовом втором событии, /events выбросил ConnectionRefusedError. После исправления
notifications/health: 20 passed in 23.12s. Полная регрессия PostgreSQL:
**79 passed in 57.25s**, включая все прежние concurrency/миграции/билеты/SSE/outbox.
Ruff check passed; format --check: 50 files formatted. Отдельный root script
также прошёл Ruff/format. uv lock --check --offline passed, 41 packages.

Clean Compose verification:
Добавлены опциональные API_PORT/FRONTEND_PORT/MAILPIT_HTTP_PORT/MAILPIT_SMTP_PORT
с прежними default значениями. scripts/verify_clean_stack.py использует Python
standard library, уникальный Compose project, приватный generated env, пять
случайных loopback ports и пустой PostgreSQL volume. Основной стек не останавливает.
Docker build cache разрешён; полностью пустой Docker daemon не заявляется.

Попытка 1 обнаружила race готовности frontend: Compose --wait без frontend
healthcheck возвращал управление до запуска Vite, первый запрос получил reset.
Добавлен healthcheck API/БД через Vite proxy и ожидание готовности в verifier.
Попытка 2 остановилась на ошибке отступов YAML при редактировании до создания
контейнеров; YAML исправлен, compose config --quiet passed. Эти реальные failed
reports сохранены отдельно. Cleanup failed в attempt-2 обусловлен тем же parse
error; ресурсы этого project не создавались.

Успешная попытка: reports/phase6-clean-stack.json, **79.78s**. Подтверждены:
миграции пустой БД, отсутствие событий до seed, повторный seed без дублей,
Alembic drift check, 20 одновременных signup → 5 confirmed / 15 waiting,
два SSE клиента, retry, FIFO promotion, отзыв старого билета, single-use check-in,
перенос и reminder в Mailpit. Остановка SMTP оставила pending с attempts, HTTP
регистрация продолжала работать; после восстановления job стал sent. Остановка
PostgreSQL дала 503 для /events и readiness; после старта/рестарта сохранились
5 confirmed / 14 waiting / 1 checked_in и прежний ticket timestamp.
В finally удалены только project containers/network/volume. Финальный docker
inventory не нашёл eventflow-verify containers/volumes, основной стек здоров.

Frontend/browser verification:
**15 Node tests passed**, TypeScript/Vite build и oxlint passed. Фактический
ORGANIZER_TOKEN не найден в frontend/dist; .env/venv/node_modules не отслеживаются.
Существующий CDP helper выделен в frontend/scripts/browser.mjs и закрывает сами
вкладки, чтобы не оставлять лишние SSE connections.

Новый smoke_phase6_browser.mjs проверяет loading/empty/503/retry через перехват
только API списка; ticket cancellation/check-in — настоящий API. Первоначальная
маска URL перехватила также Vite /src/api/events.ts, runner не мог отрисовать
loading; исправлено origin-ограничением. Это тестовая ошибка, не fake pass.
Следующий прогон выявил реальное mobile overflow; после исправления сценарий
успешен: 404, неверный organizer token, нет private link, native capacity=0,
отозванный билет не сохраняет valid-label. На 320px проверены check-in, участники,
editor, public event и private status с title из 198 символов без пробелов.
Снимок /tmp/eventflow-phase6-mobile.png сохранён и визуально просмотрен.

Полный flow Phase 5 повторён с новым helper: **passed**, регистрация видна во
второй вкладке за **925ms**, waiting → promotion, ticket/verify/check-in,
attendance, перенос, backend stop/start и SSE reconnect, mobile screenshot.
Скрипт cleanup-browser удалил только события всех записанных попыток обоих
сценариев под Event lock с проверкой UUID/названия; state-файлы удалены.
Demo/user events не изменялись, тестовые синтетические письма остаются в Mailpit.

README, requirements, architecture, decisions, testing, prompts и новый
submission.md приведены к итоговому техническому состоянию. Не заявляются
выполненными GitHub publication, личное эссе, production hosting, CI, email
ownership/recovery или полный accessibility/cross-browser audit.
Дальше кандидату: создать GitHub, проверить опубликованный clone и приложить
своё эссе из 10 предложений. Код и документация фиксируются проверенными частями.

После проверок созданы коммиты:
- 4ba3122 — backend outage handling, outbox fairness и regression tests.
- 635fc89 — UX/320px, CDP helper и браузерные проверки.
- ab830f0 — isolated Compose verifier, frontend healthcheck и настоящие reports.
Документация фиксируется отдельно; удаления docs/prompts остаются вне коммитов.

## 2026-10-26 — Interface redesign

Date/time recorded during work: 2026-10-26T11:37:11+05:00 (Asia/Qyzylorda).
Codex (GPT-6 family in environment); user-requested Impeccable installed and used.
Skill-directed finish reviewer and documenter worked in separate agent contexts.

Replaced technical foundation presentation with an event discovery flow: real
search and date filters, illustrative covers, clear event details and registration,
private ticket and management link, organizer navigation and mobile records.
Preserved email-only registration; optional questions about accounts/language had
no answer, so existing approved Russian/no-account behavior remains. No invented
prices, locations or attendance numbers. Auth and transaction guarantees unchanged.

Backend 81 tests passed, frontend 16 passed; build/lint/Ruff passed. Real browser
redesign smoke passed, two-client Phase 5 regression passed (978ms). Reviewer found
mobile table readability and authenticated 320px header overflow; both fixed and
rechecked, final scored disposition ship. Detector run once returned []; raster
provenance scan: 2 files, 0 missing. DESIGN.md and design.json document actual CSS.

Phase 6 runner required updates for SVG-backed navigation, specific ticket input,
and summary clicks. Loading text is visually hidden, so loading assertion uses
textContent. Stronger viewport overflow checks identified narrow search grid sizing
and hidden heading positioning; corrected rather than weakening assertions.

User asked about lost code. Verified worker includes ticket code in confirmation
mail. Clarified Mailpit is local, personal management URL is saved separately and
email recovery is not implemented. Ticket page copy now states those limits.
Deliberate docs/prompts deletions remain outside commits by user's instruction.

Final Phase 6 browser regression passed with pages initialized at320px before
navigation. Earlier resize attempts showed a stale mobile root width336 while body
and content bounds stayed320; fresh mobile navigation passed the strict check.
Search sizing, hidden text containment and skip-link width are bounded explicitly.
No assertion was changed to accept a wider scroll area. Frontend16/build/lint and
Ruff50 are clean after final changes. Self-hosted assets need no visitor CDN calls.

Scoped cleanup removed recorded browser smoke events only; demo/user events kept.
Commits: 0ab6aca (backend filters), 313aaa5 (UI/assets/browser checks).
The upstream font OFL is preserved verbatim, including its line21 trailing space;
Git whitespace check reports that vendor text, with no application whitespace errors.

## 2026-10-27 — README для сдачи и скриншоты

Временная метка: 2026-10-27T14:44:12+05:00, Asia/Qyzylorda.
Инструмент: Codex (семейство GPT-6 по среде), без новых субагентов.
Пользователь попросил исследовать рекомендации по README, самостоятельно снять
скриншоты и показать для проверки; CI предложен как возможный следующий шаг.

Прочитаны GitHub Docs «About the repository README file» и Make a README.
Порядок выбран под проверяющего: проблема → решение → интерфейс → запуск →
ручной сценарий → архитектура → проверки → ограничения → AI-процесс.
Подробные старые команды/API сохранены в docs/local-development.md; ссылки
скорректированы. В submission.md исправлено устаревшее утверждение об отсутствии
субагентов: указаны фактические reviewer/documenter при редизайне.

Headless Chromium/CDP снял четыре новых PNG из работающего приложения:
афиша1440×1250, мобильная390×844, dashboard1440×1050, билет1100×1100.
Все снимки визуально просмотрены. Для организатора и билета создано отдельное
событие на2 места и3 вымышленных email @example.com:2 confirmed/1 waiting.
Код билета заменён в DOM на «ДЕМО · НЕ ДЛЯ ВХОДА», личная ссылка скрыта;
исходный код приложения не изменялся. После съёмки удалены только созданные
регистрации и событие по сохранённому UUID с проверкой названия под Event lock.
Пользовательские данные сохранены. Синтетические письма могут оставаться в Mailpit.

Проверены локальные ссылки README, local-development и submission: все существуют;
PNG заголовки/размеры, git diff --check: успешно. Бизнес-код не изменён, полный
backend/frontend suite повторно не запускался; результаты26 октября подписаны
своей датой. CI workflow не добавлялся и успешный GitHub run не заявляется.
Исследованные источники:
- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes
- https://www.makeareadme.com/

Имеющиеся пользовательские изменения .gitignore и удаления docs/prompts оставлены
вне коммита этой задачи. Личный essay и GitHub публикация остаются кандидату.

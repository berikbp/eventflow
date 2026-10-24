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

# Проверки

## Воспроизводимые команды
Полные команды запуска приведены в ../README.md.

- backend: uv sync --locked; uv run pytest; uv run ruff check .;
  uv run ruff format --check .; uv lock --check.
- PostgreSQL: задать TEST_DATABASE_URL и выполнить uv run pytest.
- frontend: npm ci; npm test; npm run build; npm run lint.
- инфраструктура: docker compose config --quiet;
  docker compose up --build -d --wait; docker compose ps.
- HTTP: /health, /health/ready, frontend /api/health/ready.

Unit tests проверяют liveness, выполнение SELECT 1 и безопасный ответ 503.
Опциональный integration test использует настоящую PostgreSQL через FastAPI
lifespan; без TEST_DATABASE_URL явно skipped. Он не проверяет бизнес-логику.
Итоговые фактические результаты текущей сессии — в development-log.md.

Frontend regression tests запускаются встроенным test runner Node.js 24.
Проверяют успешный readiness через настоящий QueryClient (queryFn обязан вернуть
данные), отказ БД и неожиданный JSON. Дополнительных test dependencies нет.

## Ручная проверка Foundation
1. Открыть http://localhost:5173, дождаться успешного статуса API и PostgreSQL.
2. Нажать «Проверить снова», проверить disabled/loading.
3. Остановить db: docker compose stop db. Нажать кнопку после завершения
   текущего запроса: увидеть ошибку, /health остаётся 200, /health/ready — 503.
4. docker compose start db; повторить проверку, дождаться восстановления.
5. Проверить узкое окно браузера и неизвестный путь (404-экран SPA).
6. Открыть Mailpit на :8025; отсутствие писем ожидаемо.

## План интеграционных тестов следующих этапов
Мероприятие → регистрация → дубликат → очередь → отмена → FIFO → билет →
check-in → повторный check-in → перенос → outbox → reminders → restart.
Concurrency: два запроса на одно место и 20 запросов на 5 мест с независимыми
соединениями PostgreSQL. Отдельно одновременные отмены и продвижения.
Проверить идемпотентность, отозванные билеты, доступ и нормализацию email.

## План ручного демо в двух вкладках (пока не исполняется)
После Phase 5: открыть публичное мероприятие и dashboard организатора,
зарегистрироваться, заполнить лимит, увидеть очередь; отменить подтверждённую
регистрацию и увидеть продвижение, письмо Mailpit и новый билет.
Выполнить check-in дважды; dashboard меняется один раз. Перенести событие,
проверить SSE, уведомления и пересчёт reminders. Переподключить вкладку и
перезапустить backend/worker: состояние и задания сохраняются.
Demo data мероприятий добавлены в Phase 2; demo регистраций — после Phase 3.

## Phase 2 — мероприятия

Backend: 31 тест с TEST_DATABASE_URL. Помимо Foundation проверяются схемы/UTC,
CRUD на настоящем PostgreSQL, bearer access, 404/422, пагинация, CHECK ограничения,
schedule_version, downgrade/upgrade, Alembic drift check и повторный seed.
Без TEST_DATABASE_URL PostgreSQL-тесты явно пропускаются; остальные выполняются.
Windows использует UV_PROJECT_ENVIRONMENT=.venv-windows, WSL — своё окружение.
Миграции в тестах применяются программно к изолированным UUID-схемам, которые
удаляются в teardown. Отдельная пустая тестовая БД всё равно предпочтительна.

Frontend: npm test проверяет readiness, CRUD request/response, обработку 204,
ошибки API и локальное время ↔ UTC. npm run build проверяет TypeScript;
npm run lint — статический анализ. Это не browser end-to-end tests.

Ручной сценарий Phase 2:
1. Инициализировать .env по README, запустить Compose и app.seed.
2. На главной увидеть два demo-события, открыть детали.
3. Открыть «Организатору», проверить ошибку неверного токена, затем ввести свой
   ORGANIZER_TOKEN из .env. Создать событие с названием, описанием, датой, лимитом.
4. Увидеть success и детали, вернуться к списку. Изменить дату и вместимость.
5. Проверить пустое название, прошлую дату, 0 мест и текст длиннее лимитов.
6. Обновить страницу: повторный ввод токена ожидаем. Публичные страницы доступны.
7. Удалить только своё тестовое событие через подтверждение; оно исчезает из списка.
8. Проверить narrow viewport, loading/error/empty states. Визуальный browser QA
   агентом в этой сессии не выполнен: inventory браузеров пуст.

Выполнен живой API smoke через frontend proxy: проверка доступа, создание временной
записи, чтение, PATCH и DELETE; временная запись удалена. Demo event сохранился
после перезапуска PostgreSQL/backend. Полный UI-сценарий кликами не исполнялся.

## Phase 3 — регистрация и FIFO

Backend: **49 passed** с TEST_DATABASE_URL на PostgreSQL. Fixture database/client
вынесены в tests/conftest.py; каждый integration test получает UUID-схему и
независимые соединения NullPool. Пользовательские таблицы не очищаются.
Новые проверки включают:
- 2 конкурентных запроса на последнее место → 1 confirmed, 1 waiting.
- 20 запросов / 5 мест → 5 confirmed, 15 waiting, 20 уникальных строк и FIFO-номеров.
- 10 одинаковых retry → одна регистрация; 5 разных ключей на один email →
  один успех, четыре 409 без выдачи доступа к существующей строке.
- Одновременные отмены и повтор отмены → только первые два ожидающих продвинуты.
- Отмена одновременно с новой регистрацией и рост capacity одновременно с
  регистрацией → существующий ожидающий не пропускается.
- Запрет уменьшения capacity ниже занятых мест и DELETE с историей регистраций.
- Private read/cancel, hash вместо plaintext, отсутствие token_hash в organizer API.
- Нормализация email, CHECK/UNIQUE, закрытие участия после старта и rejoin.
- Прямые конкурентные INSERT вне API: один успех/одна ошибка при одном месте;
  rollback откатывает и Registration, и confirmed_count.
- Upgrade/downgrade/upgrade и Alembic metadata check остаются в регрессии.

Frontend: **12 passed**, build и lint проходят. Новые тесты проверяют передачу
секретов в заголовках, стабильный retry, fragment-link roundtrip, восстановление
pending attempt из sessionStorage и очистку после успеха, protected list endpoint.
Тесты используют Node runner и настоящий QueryClient в health regression;
browser end-to-end coverage не заявляется.

Ручной сценарий Phase 3 в двух вкладках:
1. Создать будущее мероприятие на 1 место; открыть его в публичной вкладке.
   Во второй вкладке войти организатором и открыть «Участники» этого события.
2. Зарегистрировать email A, сохранить личную ссылку. Увидеть confirmed;
   не позднее следующего polling (10 секунд) у организатора confirmed=1.
3. Открыть публичную страницу снова, зарегистрировать email B; увидеть waiting,
   позицию 1, сохранить вторую личную ссылку.
4. Отменить A через его ссылку. В B дождаться confirmed; организатор видит
   A cancelled, B confirmed. Повтор отмены через API не даёт нового эффекта.
5. Через ссылку A нажать rejoin: он получает waiting. Повысить capacity до 2
   у организатора: A автоматически confirmed. Попытка снизить до 1 даёт 409.
6. Изменить #token в личной ссылке: private API возвращает 404 и не даёт отменить
   запись. Повтор email без исходного ключа даёт 409, не раскрывая личную ссылку.
7. Перезагрузить личную ссылку: доступ сохраняется через fragment. Pending retry
   после потери ответа использует ту же пару email/ключ, пока доступен sessionStorage.
8. Перезапустить backend и db: статусы/очередь сохраняются; после следующего
   опроса страницы получают актуальное состояние. SSE пока не используется.

Выполнен живой API smoke через :5173/api с созданием отдельного временного события:
две регистрации, отмена A → продвижение B, rejoin A → waiting, приватное чтение,
организаторский список и запрет DELETE с историей. После restart db/backend
состояние и доступ сохранились. Тестовые записи и файл с их ключами удалены;
для очистки удалены только записи созданного smoke-event в транзакции с проверкой
его UUID/названия и Event row lock. Demo/user events не менялись.
Полный сценарий кликами не выполнялся: browser inventory пуст.

## Phase 4 — билеты

2026-10-24: 59 backend tests passed на настоящем PostgreSQL, включая 10 новых
сценариев tickets. Команда из backend (WSL):

```bash
TEST_DATABASE_URL=postgresql+asyncpg://eventflow:eventflow_local@127.0.0.1:5433/eventflow .venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
UV_CACHE_DIR=/tmp/eventflow-uv-cache uv lock --check --offline
```

Проверены выдача/retry, отсутствие билета у waiting/cancelled, доступ, нормализация
кода, отзыв, новый код при повторном подтверждении, promotion при росте capacity,
20 конкурентных входов (один новый вход), гонка отмены/check-in, UNIQUE и rollback,
backfill существующих confirmed и Alembic drift check.

Frontend: npm test, npm run build, npm run lint прошли. Дополнительно
`node --experimental-strip-types --test --test-reporter spec --test-isolation=none tests/*.test.ts`
показал 14 отдельных успешных тестов. Стандартный npm test в этой версии Node
показывает итог по четырём файлам. Это модульные проверки, не browser E2E.

Ручной сценарий:
1. Создать будущее событие на одно место, зарегистрировать A и B.
2. A видит билет по личной ссылке; B ожидает без билета.
3. Отменить A: его билет отозван, B получает новый билет.
4. Организатор: «Участники» → «Проверка билетов и check-in». Проверить старый
   код A (отозван), код B (действителен), код другого события (404).
5. Подтвердить вход B. Проверить тот же код повторно: время прежнее,
   посещаемость остаётся 1. Отмена B отклоняется, место не передаётся очереди.
6. Проверить обновление счётчика/личного статуса в пределах 10 секунд polling.

Визуальная проверка браузером в текущей сессии не выполнена: доступного
browser-инструмента нет. Запуск из полностью чистой среды остаётся Phase 6.

Compose Phase 4 пересобран и запущен. Alembic check в контейнере прошёл.
Живой API smoke через frontend proxy прошёл; после restart db/backend билет
и checked_in_at сохранились, повторный check-in не увеличил attendance.
Созданные smoke-записи удалены под Event lock с проверкой UUID/названия;
пользовательские/demo данные сохранены.

## Phase 5 — SSE и уведомления (2026-10-24)

Backend: 76 passed на PostgreSQL, включая 14 новых outbox-сценариев и 3 SSE.
После изменения heartbeat отдельно повторены 3 SSE-теста: passed.
Ruff check/format и uv lock --check прошли. Миграции roundtrip/drift входят
в регрессию; Alembic check в работающем контейнере также прошёл.

Outbox tests проверяют logical dedup, rollback, promotion, отмену/старый билет,
ошибку SMTP и backoff, истечение lease после restart, двух worker, отсутствие
Event lock во время SMTP, backfill старых confirmed, reminders после rejoin,
перенос раньше/позже и новую версию после отправленного reminder. SMTP в этих
тестах подменён функцией; фактическая Mailpit-доставка проверяется отдельно.

SSE tests: два независимых генератора получают изменения registration, promotion,
check-in и Event; initial snapshot на reconnect; отсутствие private payload;
нефиксированные/откаченные изменения не видны; heartbeat и безопасное закрытие
при сбое БД. Frontend: 15 passed, включая invalidate, reconnect, heartbeat-watchdog
и cleanup. npm run build/lint проходят.

Браузер: настоящий headless Chromium 153, две вкладки, через Vite proxy.
Успешно проверены регистрация (видна организатору за 953ms), waiting, продвижение,
билет, verify/check-in, attendance=1 и повторная проверка, перенос, остановка/
старт backend, reconnect обеих вкладок и актуальная дата/название. Проверка
обновления ограничена 5 секундами, меньше резервного polling 10 секунд.
Проверена ширина 390px без горизонтального переполнения и просмотрены screenshots
панели 1440px и личного билета 390px. Это целевой smoke, не полное browser покрытие.

При первой проверке обнаружен открытый downstream SSE после остановки API:
Vite proxy не передавал close. Исправлено; реальный shutdown/reconnect повторён.
Эмуляция offline CDP сама не обрывала существующий SSE, поэтому не считается
проверкой reconnect. Добавлен именованный heartbeat и watchdog, проверенный
mock timers без реального ожидания 25 секунд.

### Повторить целевой браузерный smoke (опционально)

Нужны работающий Compose, Node 24, Chrome с remote debugging и Docker CLI.
Скрипт создаёт отдельные события, читает токен из .env, **останавливает/запускает
backend** и закрывает ранее открытые вкладки EventFlow в этом тестовом Chrome.
Используйте отдельный профиль браузера. Пример Linux (путь к Chrome свой):

```bash
chromium --headless --remote-debugging-port=9222 --user-data-dir=/tmp/eventflow-browser about:blank
node frontend/scripts/smoke_phase5_browser.mjs
cd backend
PYTHONPATH=. uv run python scripts/smoke_phase5.py cleanup-browser --state /tmp/eventflow-phase5-browser-state.json
```

CHROME_DEBUG_URL и EVENTFLOW_URL можно переопределить. В Linux screenshots и
scoped state сохраняются в /tmp; Node использует os.tmpdir() в других ОС.
State нужен для очистки даже после неуспешной попытки. Cleanup проверяет UUID
и название, удаляет только записанные smoke events под блокировкой Event.
В текущей среде Chrome был в кеше Playwright, ему не хватало libnspr4/libnss3/
libasound2t64; они скачаны и распакованы в /tmp, системная установка не менялась.

### Проверка реальной почты и restart outbox (WSL/bash)

Запускается на локальном Compose, создаёт отдельное событие и уникальный email.
Mailpit сохраняет тестовые письма для просмотра. Из корня:

```bash
docker compose stop worker
cd backend
PYTHONPATH=. uv run python scripts/smoke_phase5.py prepare --state /tmp/eventflow-phase5-delivery-state.json
cd ..
docker compose restart db backend
docker compose up -d --wait worker
cd backend
PYTHONPATH=. uv run python scripts/smoke_phase5.py verify --keep --state /tmp/eventflow-phase5-delivery-state.json
cd ..
docker compose restart worker
cd backend
PYTHONPATH=. uv run python scripts/smoke_phase5.py verify --state /tmp/eventflow-phase5-delivery-state.json
```

prepare ожидает ровно два pending-задания. verify ждёт два sent, проверяет два
фактических Mailpit-письма (confirmation/reminder) с кодом билета; без --keep
удаляет только собственные записи и state. Не запускайте второй локальный worker
одновременно с этим тестом. При ошибке state сохраняется для повторной проверки.

Фактический restart smoke Phase 5 выполнен: prepare сохранил два pending,
PostgreSQL/backend перезапущены, worker запущен, verify нашёл два sent и два
физических Mailpit-письма с кодами. После дополнительного restart worker
повтор verify также нашёл ровно два письма. Очистка собственных событий/регистраций
и state прошла; все записанные события браузерных попыток тоже удалены через
cleanup-browser. Письма с синтетическими адресами оставлены в Mailpit как демо.
Все пять Compose-сервисов работают, worker logs не содержат ошибок,
финальный Alembic check прошёл.

## Phase 6 — стабилизация (2026-10-25)

Полный backend-прогон на настоящем PostgreSQL: **79 passed in 57.25s**.
Добавлены regression cases на недопустимую остановку обработки из-за занятого
Event, безопасный 503 обычного API при отказе БД и late ack после смены lease.
Два первых теста до исправлений действительно падали; после исправления группа
notifications/health показала 20 passed, затем прошла полная регрессия.
Frontend: **15 passed**, TypeScript/Vite build и lint прошли.
Ruff/format/uv lock прошли, runtime dependencies не добавлялись.

### Полная проверка нового Compose-проекта

```bash
python3 scripts/verify_clean_stack.py --report /tmp/eventflow-clean-stack-report.json
```

Скрипт использует только Python standard library и Docker CLI, уникальный project,
пять случайных loopback host ports, приватный env и пустой PostgreSQL volume.
Главный локальный EventFlow не останавливается. Docker build cache допускается.
В finally удаляется только временный проект/volume; отчёт не содержит секретов.

[Успешный JSON-отчёт](../reports/phase6-clean-stack.json):
- Миграции на пустой БД, отсутствие событий до seed, два idempotent seed, Alembic check.
- 20 конкурентных HTTP регистраций → 5 confirmed, 15 waiting, уникальные ID.
- Два SSE клиента, retry регистрации, FIFO promotion, отзыв и check-in только один раз.
- Перенос и реальное reminder-письмо в Mailpit.
- Остановка SMTP: HTTP регистрация работает, outbox остаётся pending с attempts;
  после восстановления SMTP — sent.
- Остановка PostgreSQL: /events и /health/ready дают 503; после старта/перезапуска
  ticket.checked_in_at, confirmed/waiting/checked_in и миграции сохраняются.
- Удаление только временного Compose-проекта, сети и volume.

Предыдущие попытки сохранены отдельно: attempt-1 обнаружила гонку готовности
frontend (Compose ещё не ждал Vite); добавлен healthcheck через API proxy.
Attempt-2 остановилась на ошибке отступов YAML во время исправления, до создания
контейнеров. После исправления compose config --quiet и полный сценарий прошли.
Cleanup failed в attempt-2 означает невозможность разобрать YAML, а не потерю
контроля над пользовательскими данными; ресурсы того project не создавались.

### UX smoke и узкий экран

После запуска отдельного Chrome с remote debugging, как в разделе Phase 5:

```bash
node frontend/scripts/smoke_phase6_browser.mjs
cd backend
PYTHONPATH=. uv run python scripts/smoke_phase5.py cleanup-browser --state /tmp/eventflow-phase6-browser-state.json
```

Новый script перехватывает **только ответы списка API** для проверки loading,
empty, 503 и успешного retry. Отозванный билет/проверка/check-in используют настоящий
API. Проверены 404, отсутствие личного ключа, неверный organizer token, native
validation capacity=0. На 320px проверены check-in, список участников, editor,
публичное мероприятие и личный статус, включая название длиной 198 символов без
пробелов. При первом прогоне обнаружено переполнение title на check-in; исправлено
наследуемым overflow-wrap. Проверки всех пяти страниц затем прошли.
Снимок /tmp/eventflow-phase6-mobile.png просмотрен визуально.

Маска interception в первой версии runner затрагивала Vite module
/src/api/events.ts; уточнена до origin + /api/events*. Это ошибка тестового
runner, не ложное прохождение loading check. Общий CDP helper теперь закрывает
тестовые вкладки; не оставляет лишние SSE-соединения после сценария.
Полный flow Phase 5 повторяется для регрессии helper/UX/reconnect.
Проверено отсутствие фактического ORGANIZER_TOKEN в frontend/dist; .env и venv/
node_modules отсутствуют среди отслеживаемых файлов.

Финальный двухвкладочный flow также прошёл с общим CDP helper:
регистрация видна организатору за **925ms**, promotion, check-in, attendance,
перенос, настоящий backend shutdown/reconnect и мобильный билет.
Cleanup-browser удалил только записанные события обоих сценариев и state-файлы.
Текущий Compose здоров, временные eventflow-verify контейнеры/volumes отсутствуют.

## UI redesign — 26 October 2026

Real PostgreSQL backend suite: **81 passed (39.96s)**; event API subset:
**8 passed (4.65s)**. Added real search/date filtering, escaping, pagination and
invalid-period coverage. Frontend: **16 passed**, TypeScript/Vite build and oxlint
passed; Ruff check and format passed (50 files).

`node frontend/scripts/smoke_redesign_browser.mjs` passed: real search, empty/reset,
date filtering, FAQ, email registration, ticket, organizer access, widths
1440/1280/390/320. Phase 5 two-client flow passed again: update visible in 978ms,
waiting/promotion/check-in/reschedule and backend restart/SSE reconnect.

Headless Chromium screenshots were visually reviewed for home, event, ticket,
organizer and error states. Impeccable finish reviewer scored mobile participant
records, authenticated header wrapping and seed corroboration resolved (ship).
This is a scoped review, not a complete accessibility/cross-browser certification.
Local captures are ignored because temporary tickets contain private credentials.

Phase 6 browser regression also passed after adapting the runner to initialize
320px emulation before navigating: loading, empty, 503/retry, 404, invalid token,
capacity validation, revoked check-in and five long-title layouts. Chromium resize
attempts reported root width336 while all content bounds/body remained320; fresh
mobile navigation passed strict document scrollWidth checks. This runner behavior
is recorded separately from the fixed search/header/table layout issues.

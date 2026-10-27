# Тестирование EventFlow

## Backend

Нужны uv, Python 3.12 и настоящий PostgreSQL. Из корня запустите
`docker compose up -d --wait db`, затем из `backend`:

```bash
uv sync --locked
TEST_DATABASE_URL=postgresql+asyncpg://eventflow:eventflow_local@127.0.0.1:5433/eventflow uv run pytest
uv run ruff check .
uv run ruff format --check .
uv lock --check
```

При изменённых настройках `.env` укажите соответствующий URL. В PowerShell
задайте `$env:TEST_DATABASE_URL = "postgresql+asyncpg://eventflow:eventflow_local@127.0.0.1:5433/eventflow"`
перед `uv run pytest`. Для Windows/WSL используйте отдельные виртуальные среды.
Без TEST_DATABASE_URL интеграционные тесты пропускаются. Каждый тест создаёт
отдельную UUID-схему и удаляет только её; роль БД должна иметь CREATE SCHEMA.

Покрытие: CRUD, валидация и доступ; повторные email; последнее место; 20 запросов
на 5 мест; FIFO и конкурентные отмены; rollback; ограничения БД; выдача/отзыв
билета; повторный и конкурентный check-in; outbox, retries, reminders, перенос,
устаревшие задания и восстановление после ошибок.

## Frontend

Node.js 24, из `frontend`:

```bash
npm ci
npm test
npm run build
npm run lint
```

Проверяются API-клиент, обработка ошибок, секреты в заголовках/fragment,
идемпотентные повторы, даты и инвалидация запросов при SSE/reconnect.

## Изолированный запуск Compose

Из корня, Python 3.12+ и Docker Compose:

```bash
python3 scripts/verify_clean_stack.py --report /tmp/eventflow-clean-stack-report.json
```

В Windows используйте `py -3.12` и свой путь отчёта. Скрипт создаёт уникальный
Compose-проект, новый PostgreSQL volume и случайные loopback-порты. Проверяет
миграции, seed, concurrency20/5, FIFO, билеты, два SSE-клиента, Mailpit, отказ SMTP,
readiness503 при отказе БД и сохранение после restart. В finally удаляет только
свой проект/volume. Основное окружение сохраняется. Docker build cache разрешён.

## Проверка в браузере

Сначала запустите приложение по [README](../README.md). Откройте афишу и панель
организатора в разных вкладках, Mailpit — на http://localhost:8025.

1. Создайте событие на одно место, дата — в будущем.
2. Зарегистрируйте A, сохраните личную ссылку и проверьте билет/письмо.
3. Зарегистрируйте B: очередь1. Организатор видит изменения автоматически.
4. Отмените A: билет отозван, B получает место, новый билет и письмо.
5. Проверьте билет B и подтвердите вход дважды: посещаемость остаётся1.
6. Перенесите событие: новое расписание видно обеим вкладкам, письмо в Mailpit.
   Если до начала менее24 часов, напоминание отправляется сразу.
7. Перезапустите backend: SSE переподключается, данные восстанавливаются из API.
8. Проверьте мобильную ширину, неверный токен, неизвестную страницу и empty/error states.

### Автоматизация Chromium/CDP

Нужен Chrome/Chromium с отдельным временным профилем и CDP на9222:

```bash
chromium --headless --remote-debugging-port=9222 --user-data-dir=/tmp/eventflow-browser about:blank
node frontend/scripts/smoke_phase5_browser.mjs
node frontend/scripts/smoke_phase6_browser.mjs
```

Phase5 проверяет две вкладки, очередь, promotion, check-in, перенос и реальный
stop/start backend. Phase6 проверяет loading/empty/503/retry, доступ, валидацию,
отозванный билет и пять страниц на320px. CHROME_DEBUG_URL и EVENTFLOW_URL можно
переопределить. Docker должен быть доступен runner для stop/start.

После сценариев из `backend`:

```bash
PYTHONPATH=. uv run python scripts/smoke_phase5.py cleanup-browser --state /tmp/eventflow-phase5-browser-state.json
PYTHONPATH=. uv run python scripts/smoke_phase5.py cleanup-browser --state /tmp/eventflow-phase6-browser-state.json
```

Cleanup проверяет записанные UUID/названия и удаляет только тестовые события под
Event lock. Если сценарий прерван, сохраните state для очистки. Вне Linux пути
берите из системного временного каталога. Письма вымышленных адресов могут остаться
в Mailpit. Не запускайте несколько сценариев с одним state одновременно.

### Доставка писем после restart

Локальный Compose, из корня:

```bash
docker compose stop worker
cd backend
PYTHONPATH=. uv run python scripts/smoke_phase5.py prepare --state /tmp/eventflow-delivery-state.json
cd ..
docker compose restart db backend
docker compose up -d --wait worker
cd backend
PYTHONPATH=. uv run python scripts/smoke_phase5.py verify --keep --state /tmp/eventflow-delivery-state.json
cd ..
docker compose restart worker
cd backend
PYTHONPATH=. uv run python scripts/smoke_phase5.py verify --state /tmp/eventflow-delivery-state.json
```

Prepare создаёт собственные записи с pending-заданиями. Verify проверяет sent
и реальные письма Mailpit; без --keep удаляет собственные записи и state.
Не запускайте дополнительный локальный worker одновременно с этим сценарием.

## Зафиксированные результаты

- 26 октября2026: backend **81 passed**, frontend **16 passed**, build/lint/Ruff passed.
- Браузерные сценарии: регистрация, очередь/promotion, check-in, перенос,
  две вкладки и SSE reconnect; мобильные и ошибочные состояния проверены.
- 25 октября2026: изолированный Compose успешно проверен с пустым volume;
  [машинный отчёт](../reports/phase6-clean-stack.json).

Это локальные результаты, не подтверждение GitHub CI. Полный cross-browser
и accessibility audit не выполнялся.

# EventFlow

Система регистрации на мероприятия для тестового задания MadDevs №9.
Текущий этап: **Phase 1 — Foundation**. Реализованы FastAPI, проверка PostgreSQL,
React/TypeScript/Vite и локальная Docker-инфраструктура. Регистрация, мероприятия,
билеты, авторизация, SSE и отправка уведомлений пока не реализованы.

## Быстрый запуск (PowerShell, из корня)

Требуются Docker Desktop с Linux containers и Docker Compose v2.

```powershell
Copy-Item .env.example .env
docker compose up --build -d --wait
docker compose ps
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/health/ready
Invoke-RestMethod http://localhost:5173/api/health/ready
```

- Frontend: http://localhost:5173
- OpenAPI: http://localhost:8000/docs
- Mailpit: http://localhost:8025 (SMTP: localhost:1025)
- PostgreSQL: localhost:5433

Compose имеет локальные значения по умолчанию и работает без .env.
.env нужен прежде всего для запуска backend вне контейнера.
При изменении POSTGRES_PORT обновите порт в DATABASE_URL для локального backend.
Пароли с URL-спецсимволами требуют percent-encoding в URL; для Compose используйте
локальный пароль без таких символов. Переменные и стандартные пароли предназначены
только для локальной разработки. Все опубликованные порты привязаны к loopback.

Frontend использует /api через Vite proxy. В контейнере адрес backend — backend:8000,
на хосте — 127.0.0.1:8000. CORS для этого сценария не нужен.

```powershell
docker compose logs --tail 100
docker compose down
```

Именованный volume сохраняет PostgreSQL после down/up. Не используйте down -v,
если хотите сохранить данные. Изменение POSTGRES_PASSWORD в .env не меняет пароль
уже инициализированной БД.

## Разработка без контейнеров приложения

Требуются Python 3.12, uv и Node.js 24 / npm. Сначала из корня:

```powershell
Copy-Item .env.example .env
docker compose up -d --wait db mailpit
cd backend
uv sync --locked
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Во втором терминале из корня:

```powershell
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Не запускайте контейнеры frontend/backend одновременно с локальными процессами
на тех же портах. DATABASE_URL обязателен: читается из корневого .env либо окружения.

## Проверки

Из корня:

```powershell
docker compose config --quiet
cd backend
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv lock --check
```

Реальная БД (при запущенном Compose db; из backend):

```powershell
$env:TEST_DATABASE_URL = "postgresql+asyncpg://eventflow:eventflow_local@127.0.0.1:5433/eventflow"
uv run pytest
Remove-Item Env:TEST_DATABASE_URL
```

Frontend (из frontend):

```powershell
npm ci
npm test
npm run build
npm run lint
```

Без TEST_DATABASE_URL интеграционный тест явно пропускается.
Тесты Foundation не проверяют конкурентную регистрацию — её ещё нет.

## Структура и документация

- backend/app: API, конфигурация, lifecycle SQLAlchemy async engine.
- backend/tests: health, ошибки БД, опциональный тест настоящего PostgreSQL.
- frontend/src: начальная страница с состояниями загрузки/ошибки/успеха.
- compose.yaml: db, backend, frontend, Mailpit.
- [Требования](docs/requirements.md), [архитектура](docs/architecture.md),
  [решения](docs/decisions.md), [проверки](docs/testing.md),
  [журнал](docs/development-log.md), [промпты](docs/agent-prompts.md).

Dockerfile frontend собирает приложение для проверки, а запускает Vite dev server:
это локальная среда, не production deployment. Mailpit только подготовлен;
приложение пока не отправляет письма. Таблиц и миграций ещё нет.

Использован генератор create-vite 9.3.0, шаблон react-ts. Backend основан на
существующей uv-заготовке пользователя; зависимости управляются только uv.
Следующий этап: модели, Alembic, управление мероприятиями и минимальный доступ
организатора. Дедлайн задания: 2 ноября 2026.

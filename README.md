# EventFlow

Система регистрации на мероприятия для тестового задания MadDevs №9.
Текущий этап: **Phase 3 — Registration & Waiting List**. Реализованы CRUD
мероприятий, регистрация по email, FIFO-очередь, отмена и повторное участие,
защищённые личные ссылки и список участников для организатора.
Билеты/check-in, SSE и email-уведомления пока не реализованы.

## Быстрый запуск (PowerShell, из корня)

Требуются Docker Desktop с Linux containers и Docker Compose v2.

```powershell
cd backend
$env:UV_PROJECT_ENVIRONMENT = ".venv-windows"
uv sync --locked
uv run python -m app.setup_local
cd ..
docker compose up --build -d --wait
docker compose exec backend /app/.venv/bin/python -m app.seed
docker compose ps
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/health/ready
Invoke-RestMethod http://localhost:5173/api/health/ready
```

- Frontend: http://localhost:5173
- Организатор: http://localhost:5173/organizer
- Проверка доступности: http://localhost:5173/system
- OpenAPI: http://localhost:8000/docs
- Mailpit: http://localhost:8025 (SMTP: localhost:1025)
- PostgreSQL: localhost:5433

Для полного сценария требуется uv и Python 3.12 только на этапе setup_local.
Если нужен исключительно Docker, скопируйте .env.example в .env, задайте в нём
ORGANIZER_TOKEN — случайный секрет длиной не менее 32 символов — и выполните
docker compose up --build -d --wait. Не перезаписывайте существующий .env.
setup_local создаёт .env из примера, добавляет случайный токен и сохраняет
существующие настройки. Повторный запуск не меняет непустой токен и не печатает его.
Вход: откройте .env в редакторе, скопируйте ORGANIZER_TOKEN и введите на странице
«Организатору». Токен не включён в frontend bundle и не сохраняется в browser storage.
После обновления страницы нужно ввести его снова.

Без токена Compose запускается, но запись отключена (503). Все публичные страницы
доступны без входа. Сейчас один общий организатор управляет всеми мероприятиями;
личных аккаунтов и разделения по владельцам пока нет.
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
cd backend
$env:UV_PROJECT_ENVIRONMENT = ".venv-windows"
uv sync --locked
uv run python -m app.setup_local
cd ..
docker compose up -d --wait db mailpit
cd backend
uv run alembic upgrade head
uv run python -m app.seed
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
$env:UV_PROJECT_ENVIRONMENT = ".venv-windows"
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
Интеграционные тесты API применяют миграции в отдельных UUID-схемах PostgreSQL
и удаляют только эти схемы. Пользовательские таблицы не очищаются. Нужна роль
с правом CREATE SCHEMA. Проверяются 2 запроса на последнее место и 20 запросов
на 5 мест с независимыми PostgreSQL-соединениями, одновременные отмены/продвижение,
дубликаты email, rollback и ограничения вместимости даже при прямом INSERT.

## Структура и документация

- backend/app: API, схемы, модели, сервисы, SQLAlchemy sessions, доступ организатора.
- backend/alembic: миграция 0001_events, upgrade/downgrade.
- backend/tests: схемы, доступ, health и CRUD на настоящем PostgreSQL.
- frontend/src: список, детали, формы организатора и страница статуса системы.
- compose.yaml: db, backend, frontend, Mailpit.
- [Требования](docs/requirements.md), [архитектура](docs/architecture.md),
  [решения](docs/decisions.md), [проверки](docs/testing.md),
  [журнал](docs/development-log.md), [промпты](docs/agent-prompts.md).

Dockerfile frontend собирает приложение для проверки, а запускает Vite dev server:
это локальная среда, не production deployment. Mailpit только подготовлен;
приложение пока не отправляет письма. Backend контейнер применяет миграции
перед запуском API; эта схема старта рассчитана на один локальный экземпляр.

Использован генератор create-vite 9.3.0, шаблон react-ts. Backend основан на
существующей uv-заготовке пользователя; зависимости управляются только uv.
Следующий этап: билеты, уникальные коды и одноразовый check-in.
Дедлайн задания: 2 ноября 2026.

## API мероприятий

| Метод | Путь | Доступ |
| --- | --- | --- |
| GET | /events?limit=20&offset=0 | Публичный список |
| GET | /events/{uuid} | Публичные детали |
| POST | /events | Bearer ORGANIZER_TOKEN |
| PATCH | /events/{uuid} | Bearer ORGANIZER_TOKEN |
| DELETE | /events/{uuid} | Bearer ORGANIZER_TOKEN |
| GET | /organizer/session | Проверка Bearer токена |

Создание: title (1–200 символов), description (до 10000), capacity
(целое 1–1000000), starts_at (будущая дата с timezone). Текст обрезается по краям,
дата нормализуется в UTC. PATCH меняет только переданные поля; null и пустой
PATCH отклоняются. Новая дата должна быть в будущем, остальные поля можно
редактировать у прошедшего события. При фактическом переносе растёт schedule_version.
Уведомления и пересчёт напоминаний при переносе появятся в Phase 5.

Seed создаёт два демонстрационных события со стабильными UUID; повторный запуск
не изменяет существующие записи. Они назначаются через 7 и 14 дней от первого
запуска seed. Это не реальные мероприятия.

В PowerShell используйте .venv-windows, если тот же каталог открыт в WSL.
В WSL используйте обычный uv sync --locked без Windows-переменной
UV_PROJECT_ENVIRONMENT. Не используйте одну .venv между Windows и Linux.

## Регистрация и очередь — Phase 3

Откройте страницу мероприятия, введите email. При наличии места статус будет
confirmed, иначе waiting. Позиция в очереди и статус доступны по личной ссылке.
Сохраните её: ссылка нужна для отмены и повторного участия. Билетов и писем пока нет.
После отмены подтверждённого участия первый ожидающий автоматически получает место
в той же транзакции. Нажатие «Зарегистрироваться снова» помещает отменённую запись
в конец очереди либо сразу подтверждает её, если очередь пуста и есть место.

| Метод | Путь | Доступ |
| --- | --- | --- |
| GET | /events/{id}/availability | Публичные счётчики |
| POST | /events/{id}/registrations | JSON email + X-Registration-Token |
| GET | /registrations/{id} | Bearer ключ участника |
| POST | /registrations/{id}/cancel | Bearer ключ участника |
| POST | /registrations/{id}/rejoin | Bearer ключ участника |
| GET | /events/{id}/registrations?limit=20&offset=0 | Bearer ORGANIZER_TOKEN |

UI генерирует ключ из 32 случайных байтов через Web Crypto. API ожидает
X-Registration-Token из 43–128 URL-safe символов. При retry используйте тот же
ключ и email: вернётся существующая запись, а не новое место. Другой ключ с тем же
нормализованным email получает 409 без раскрытия ID или данных управления.
Повтор исходного POST после отмены возвращает cancelled; только явный rejoin
возобновляет участие. Email обрезается по краям и приводится к нижнему регистру
после валидации EmailStr; в БД действует UNIQUE(event_id,email).

В БД хранится SHA-256 ключа. Личная ссылка использует #token=..., а не query string:
fragment не отправляется в HTTP-запросе. API получает секрет в заголовке.
Личная ссылка остаётся в истории/закладках браузера, поэтому не публикуйте её.
Вкладка временно сохраняет незавершённую попытку в sessionStorage для retry после
перезагрузки и очищает её после успеха; при блокировке storage остаётся retry
в памяти. Восстановления потерянной ссылки и проверки владения email пока нет.

Все изменения мест берут SELECT FOR UPDATE на Event. Монотонный queue_order
задаётся под этой блокировкой. PostgreSQL trigger обновляет confirmed_count
в транзакции с Registration; CHECK запрещает count < 0 и count > capacity.
Функции API не изменяют счётчик вручную. DB-trigger также отклоняет переполнение
при прямом INSERT в registrations, но не предназначен для защиты от администратора,
отключающего триггеры или вручную переписывающего счётчик.

Уменьшение capacity ниже confirmed_count возвращает 409; увеличение продвигает
очередь. DELETE события запрещён при любой истории регистраций, включая cancelled.
После начала события новые регистрации, отмены и rejoin закрываются; чтение
и безопасные повторы уже завершённых операций сохраняются.

Организатор видит участников из карточки «Участники» или со страницы редактирования.
Счётчики, список и личный статус опрашиваются раз в 10 секунд. Это polling,
SSE появится в Phase 5. Полный ручной сценарий — в docs/testing.md.

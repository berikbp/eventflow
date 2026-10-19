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

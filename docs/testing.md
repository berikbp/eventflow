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

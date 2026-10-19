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
Seed/demo data появятся после создания схемы.

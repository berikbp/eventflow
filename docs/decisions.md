# Решения

Дата проектирования: 2026-10-19, Asia/Qyzylorda (UTC+05:00).
Статус будущих решений — предложено, реализация проверяется по этапам.

1. FastAPI + Pydantic: заданный стек, типизированные API и OpenAPI.
2. PostgreSQL: транзакции, ограничения, блокировки и реальные concurrency tests.
   SQLite не заменяет PostgreSQL для проверки конкурентного доступа.
3. uv: обязательное требование; uv.lock фиксируется, воспроизводимая установка
   через uv sync --locked. Исходная uv-заготовка перенесена в backend.
4. SQLAlchemy 2 async + asyncpg: согласованы с async FastAPI и будущим SSE.
   Новая операция получает своё соединение/сессию, не делит AsyncSession.
5. Modular monolith: отдельные API, настройки и будущие сервисы без микросервисов.
6. Liveness отдельно от readiness: живой HTTP-процесс может сообщить отказ БД.
   Readiness ограничен 5 секундами и возвращает безопасный 503.
7. Vite proxy: одинаковые /api URL для browser и Compose, без широкого CORS.
   Vite dev server только для локальной разработки; production hosting не включён.
8. SSE вместо WebSocket (план): серверные изменения однонаправленны; после
   reconnect клиент читает snapshot. HTTP используется для пользовательских действий.
9. Event row lock (план): проще для объяснения и проверки вместимости/FIFO,
   чем optimistic retry и сложные распределённые блокировки. Механизм обязателен
   для всех операций с количеством мест, включая редактирование вместимости.
10. Database outbox (план): надёжное сохранение задания в бизнес-транзакции,
    локальный worker без Redis/Celery. SMTP delivery остаётся at-least-once.
11. Mailpit: эмуляция SMTP и просмотр писем локально без внешних аккаунтов.
12. Миграции вместе с моделями в Phase 2: в Foundation таблиц нет, пустая
    миграция не нужна. Alembic уже в зависимостях.

Официальные источники, просмотренные в этой сессии:
- https://docs.astral.sh/uv/guides/integration/docker/
- https://docs.astral.sh/uv/concepts/projects/sync/
- https://vite.dev/guide/
- https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html

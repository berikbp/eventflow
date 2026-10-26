import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { listEvents } from "../api/events";
import { formatDate } from "../lib/dates";
import { ErrorMessage, Loading } from "../components/Feedback";
import { EventVisual, DateBlock } from "../components/EventVisual";
import { Icon } from "../components/Icon";

function EventSearch({
  value,
  onSearch,
}: {
  value: string;
  onSearch: (value: string) => void;
}) {
  const [search, setSearch] = useState(value);
  return (
    <form
      className="search-field"
      role="search"
      onSubmit={(e) => {
        e.preventDefault();
        onSearch(search.trim());
      }}
    >
      <Icon name="search" />
      <input
        aria-label="Поиск мероприятия"
        placeholder="Название или тема события"
        value={search}
        maxLength={200}
        onChange={(e) => setSearch(e.target.value)}
      />
      {search && (
        <button
          className="icon-button"
          type="button"
          aria-label="Очистить поиск"
          onClick={() => {
            setSearch("");
            onSearch("");
          }}
        >
          <Icon name="close" />
        </button>
      )}
      <button className="search-submit" aria-label="Найти события">
        <Icon name="arrow" />
      </button>
    </form>
  );
}

export function EventList({ manage = false }: { manage?: boolean }) {
  const location = useLocation();
  const [params, setParams] = useSearchParams();
  const q = params.get("q") || "";
  const rawPeriod = params.get("period") || "all";
  const period = ["all", "week", "month"].includes(rawPeriod)
    ? rawPeriod
    : "all";
  const rawOffset = Number(params.get("offset"));
  const offset = Number.isFinite(rawOffset)
    ? Math.max(0, Math.floor(rawOffset))
    : 0;
  const [now] = useState(() => new Date());
  const after = !manage ? now.toISOString() : undefined;
  const before =
    period === "week"
      ? new Date(now.getTime() + 7 * 86400000).toISOString()
      : period === "month"
        ? new Date(now.getFullYear(), now.getMonth() + 1, 1).toISOString()
        : undefined;
  const query = useQuery({
    queryKey: ["events", offset, q, period, manage],
    queryFn: () => listEvents(offset, { q, after, before }),
    refetchInterval: 10000,
  });
  function filter(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== "offset") next.delete("offset");
    setParams(next, { preventScrollReset: true });
  }
  const filtered = !!q || period !== "all";
  return (
    <>
      {!manage && (
        <section
          className="discovery-hero page-width"
          aria-labelledby="discovery-title"
        >
          <div className="hero-copy">
            <h1 id="discovery-title">
              Хорошие события.
              <br />
              <span>Ваши люди.</span>
            </h1>
            <p>
              Встречи, новые идеи и впечатления, ради которых стоит выйти из
              дома. Найдите событие — и станьте его частью.
            </p>
            <a className="button button-primary" href="#events">
              Выбрать событие <Icon name="arrow" />
            </a>
            <div className="hero-assurance">
              <Icon name="ticket" />
              <span>Билет по email. Без создания аккаунта.</span>
            </div>
          </div>
          <div className="hero-photo">
            <img
              src="/assets/photos/community.jpg"
              alt="Люди общаются на встрече сообщества"
              fetchPriority="high"
            />
            <div className="hero-photo-note">
              <span>
                Всё начинается
                <br />
                со встречи.
              </span>
              <Icon name="arrow" />
            </div>
          </div>
        </section>
      )}
      <main
        className={`catalog page-width ${manage ? "workspace" : ""}`}
        id="events"
      >
        <div className="page-heading">
          <div>
            <h1 className={manage ? "" : "visually-hidden"}>
              {manage ? "Ваши мероприятия" : "Афиша мероприятий"}
            </h1>
            {manage && (
              <p className="intro">
                Всё для вашей следующей встречи: расписание, участники и билеты.
              </p>
            )}
          </div>
          {manage && (
            <Link className="button button-primary" to="/organizer/events/new">
              <Icon name="plus" /> Создать мероприятие
            </Link>
          )}
        </div>
        {location.state?.notice && (
          <p className="notice success" role="status">
            <Icon name="check" />
            {location.state.notice}
          </p>
        )}
        <div className="catalog-heading">
          <h2>
            {manage
              ? "Все мероприятия"
              : filtered
                ? "Результаты поиска"
                : "Ближайшие события"}
          </h2>
          {query.data && !query.isError && (
            <span className="muted">
              {query.data.total}{" "}
              {
                (
                  {
                    one: "событие",
                    few: "события",
                    many: "событий",
                    other: "события",
                  } as Record<string, string>
                )[new Intl.PluralRules("ru").select(query.data.total)]
              }
            </span>
          )}
        </div>
        <div className="catalog-toolbar">
          <EventSearch
            key={`${q}:${period}`}
            value={q}
            onSearch={(value) => filter("q", value)}
          />
          <div className="date-filter">
            <Icon name="calendar" />
            <select
              aria-label="Период мероприятий"
              value={period}
              onChange={(e) => filter("period", e.target.value)}
            >
              <option value="all">Любая дата</option>
              <option value="week">Ближайшие 7 дней</option>
              <option value="month">В этом месяце</option>
            </select>
          </div>
        </div>
        {query.isPending && <Loading />}
        {query.isError && (
          <section className="empty-state">
            <ErrorMessage error={query.error} />
            <button onClick={() => void query.refetch()}>Повторить</button>
          </section>
        )}
        {query.data && !query.isError && (
          <>
            {query.data.items.length === 0 ? (
              <section className="empty-state">
                <Icon name="calendar" />
                <h2>
                  {filtered
                    ? "Событий по вашему запросу нет"
                    : offset
                      ? "Здесь пока пусто"
                      : "Мероприятий пока нет"}
                </h2>
                <p>
                  {filtered
                    ? "Попробуйте другую тему или выберите другой период."
                    : manage
                      ? "Создайте первое мероприятие — и пригласите участников."
                      : "Новые встречи появятся здесь. А пока узнайте, как получить билет."}
                </p>
                {filtered ? (
                  <button
                    className="secondary"
                    onClick={() => {
                      setParams({});
                    }}
                  >
                    Сбросить фильтры
                  </button>
                ) : manage ? (
                  <Link className="button" to="/organizer/events/new">
                    Создать мероприятие
                  </Link>
                ) : (
                  <a className="text-link" href="#how-it-works">
                    Как это работает <Icon name="arrow" />
                  </a>
                )}
              </section>
            ) : manage ? (
              <div className="organizer-list">
                {query.data.items.map((event) => (
                  <article key={event.id} className="organizer-event">
                    <DateBlock date={event.starts_at} />
                    <div className="organizer-event-content">
                      <h3>
                        <Link to={`/organizer/events/${event.id}/participants`}>
                          {event.title}
                        </Link>
                      </h3>
                      <p>
                        <Icon name="clock" /> {formatDate(event.starts_at)}
                      </p>
                    </div>
                    <div className="occupancy">
                      <span>
                        {event.confirmed_count}{" "}
                        <span className="muted">/ {event.capacity} мест</span>
                      </span>
                      <meter
                        min="0"
                        max={event.capacity}
                        value={event.confirmed_count}
                        aria-label="Занятые места"
                      />
                    </div>
                    <Link
                      className="button secondary"
                      to={`/organizer/events/${event.id}/participants`}
                    >
                      Участники <Icon name="arrow" />
                    </Link>
                    <Link
                      className="icon-button"
                      to={`/organizer/events/${event.id}/edit`}
                      aria-label={`Редактировать ${event.title}`}
                    >
                      <Icon name="edit" />
                    </Link>
                  </article>
                ))}
              </div>
            ) : (
              <div className="event-grid">
                {query.data.items.map((event) => (
                  <article key={event.id} className="event-card">
                    <Link
                      className="event-image-link"
                      to={`/events/${event.id}`}
                      aria-label={`Подробнее: ${event.title}`}
                    >
                      <EventVisual event={event} />
                    </Link>
                    <div className="event-card-content">
                      <div className="event-card-meta">
                        <time dateTime={event.starts_at}>
                          {new Date(event.starts_at).toLocaleDateString(
                            "ru-RU",
                            {
                              weekday: "short",
                              hour: "2-digit",
                              minute: "2-digit",
                            },
                          )}
                        </time>
                        <span
                          className={`status-pill ${event.confirmed_count >= event.capacity ? "waiting" : ""}`}
                        >
                          {event.confirmed_count >= event.capacity
                            ? "Лист ожидания"
                            : "Есть места"}
                        </span>
                      </div>
                      <h3>
                        <Link to={`/events/${event.id}`}>{event.title}</Link>
                      </h3>
                      <p className="preview">
                        {event.description ||
                          "Откройте событие, чтобы узнать подробности и забронировать место."}
                      </p>
                      <div className="card-footer">
                        <span>
                          <Icon name="people" />
                          {event.capacity - event.confirmed_count} из{" "}
                          {event.capacity} мест свободно
                        </span>
                        <Link className="text-link" to={`/events/${event.id}`}>
                          Подробнее <Icon name="arrow" />
                        </Link>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            )}
            {(offset > 0 || query.data.total > 20) && (
              <nav className="pagination" aria-label="Страницы мероприятий">
                <button
                  className="secondary"
                  disabled={offset === 0}
                  onClick={() =>
                    filter("offset", String(Math.max(0, offset - 20)))
                  }
                >
                  Назад
                </button>
                <span>Страница {Math.floor(offset / 20) + 1}</span>
                <button
                  className="secondary"
                  disabled={offset + 20 >= query.data.total}
                  onClick={() => {
                    const next = new URLSearchParams(params);
                    next.set("offset", String(offset + 20));
                    setParams(next, { preventScrollReset: true });
                  }}
                >
                  Далее
                </button>
              </nav>
            )}
          </>
        )}
      </main>
      {!manage && (
        <>
          <section className="how-section page-width" id="how-it-works">
            <div className="section-heading">
              <h2>
                Из «хочу пойти» —<br />в «увидимся там».
              </h2>
              <p>
                Аккаунт создавать не нужно.
                <br />А зарегистрироваться на событие — нужно.
              </p>
            </div>
            <ol className="how-steps">
              <li>
                <span className="step-number">1</span>
                <h3>Найдите своё событие</h3>
                <p>
                  Выберите интересную встречу и посмотрите дату и свободные
                  места.
                </p>
              </li>
              <li>
                <span className="step-number">2</span>
                <h3>Получите билет по email</h3>
                <p>
                  Зарегистрируйтесь на событие. Билет придёт после подтверждения
                  места.
                </p>
              </li>
              <li>
                <span className="step-number">3</span>
                <h3>Покажите код на входе</h3>
                <p>
                  Организатор проверит билет и отметит ваш вход. Всё, вы на
                  месте.
                </p>
              </li>
            </ol>
          </section>
          <section className="organizer-callout page-width">
            <div>
              <h2>
                Собирайте людей.
                <br />
                <span>Мы поможем с остальным.</span>
              </h2>
              <p>Регистрация, лист ожидания и билеты — в одном месте.</p>
            </div>
            <Link className="button button-lime" to="/organizer/events/new">
              Создать мероприятие <Icon name="arrow" />
            </Link>
          </section>
          <section className="faq-section page-width">
            <h2>Перед тем как пойти</h2>
            <div>
              <details>
                <summary>Можно прийти без регистрации?</summary>
                <p>
                  Для входа нужен действующий билет. Зарегистрируйтесь на
                  странице события по email: если место есть, вы получите билет.
                  Если мест нет, попадёте в лист ожидания.
                </p>
              </details>
              <details>
                <summary>Нужно ли создавать аккаунт?</summary>
                <p>
                  Нет. Регистрация на событие и аккаунт — разные вещи.
                  Достаточно email; статус и отмена доступны по личной ссылке,
                  которую нужно сохранить после регистрации.
                </p>
              </details>
              <details>
                <summary>Что, если все места заняты?</summary>
                <p>
                  Присоединитесь к листу ожидания. Когда место освободится,
                  первый в очереди автоматически получит билет и уведомление по
                  email.
                </p>
              </details>
            </div>
          </section>
        </>
      )}
    </>
  );
}

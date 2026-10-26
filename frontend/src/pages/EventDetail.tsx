import { useQuery } from "@tanstack/react-query";
import { Link, useLocation, useParams } from "react-router-dom";
import { getEvent } from "../api/events";
import { formatDate } from "../lib/dates";
import { ErrorMessage, Loading } from "../components/Feedback";
import { EventRegistration } from "../components/EventRegistration";
import { EventVisual } from "../components/EventVisual";
import { Icon } from "../components/Icon";

export function EventDetail({ token }: { token: string }) {
  const { id = "" } = useParams();
  const location = useLocation();
  const query = useQuery({
    queryKey: ["event", id],
    queryFn: () => getEvent(id),
    refetchInterval: 10000,
  });
  return (
    <main className="event-detail">
      <Link className="breadcrumb" to="/">
        <Icon name="back" />
        Все мероприятия
      </Link>
      {query.isPending && <Loading />}
      {query.isError && (
        <section className="empty-state">
          <ErrorMessage error={query.error} />
          <button onClick={() => void query.refetch()}>Повторить</button>
        </section>
      )}
      {query.data && !query.isError && (
        <>
          {location.state?.notice && (
            <p role="status" className="notice success">
              <Icon name="check" />
              {location.state.notice}
            </p>
          )}
          <EventVisual event={query.data} detail />
          <h1>{query.data.title}</h1>
          <a className="button registration-jump" href="#registration-title">
            <Icon name="ticket" />
            Получить билет
          </a>
          <div className="detail-grid">
            <div className="detail-content">
              <div className="detail-meta">
                <div>
                  <Icon name="calendar" />
                  <time dateTime={query.data.starts_at}>
                    {formatDate(query.data.starts_at)}
                  </time>
                </div>
                <div>
                  <Icon name="people" />
                  До {query.data.capacity} участников
                </div>
              </div>
              <h2>Об этом событии</h2>
              <p className="description">
                {query.data.description ||
                  "Организатор пока не добавил описание. Дата и доступность мест указаны на этой странице."}
              </p>
              <p className="footnote">
                Время указано в часовом поясе вашего устройства:{" "}
                {Intl.DateTimeFormat().resolvedOptions().timeZone}.
              </p>
              <section className="detail-how">
                <h3>Как попасть на мероприятие?</h3>
                <p>
                  Зарегистрируйтесь по email и получите билет после
                  подтверждения места. На входе покажите код организатору.
                  Создавать аккаунт не нужно, но действующий билет обязателен.
                </p>
              </section>
              {token && (
                <div className="organizer-tools">
                  <Link to={`/organizer/events/${id}/edit`}>
                    Редактировать мероприятие
                  </Link>
                  <Link to={`/organizer/events/${id}/participants`}>
                    Список участников и очередь
                  </Link>
                </div>
              )}
            </div>
            <EventRegistration key={id} eventId={id} />
          </div>
        </>
      )}
    </main>
  );
}

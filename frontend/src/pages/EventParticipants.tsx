import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import {
  getAvailability,
  listRegistrations,
  registrationLabels,
} from "../api/registrations";
import { getEvent } from "../api/events";
import { ErrorMessage, Loading } from "../components/Feedback";
import { Icon } from "../components/Icon";

export function EventParticipants({ token }: { token: string }) {
  const { id = "" } = useParams();
  const [offset, setOffset] = useState(0);
  const event = useQuery({
    queryKey: ["event", id],
    queryFn: () => getEvent(id),
    refetchInterval: 10000,
  });
  const availability = useQuery({
    queryKey: ["availability", id],
    queryFn: () => getAvailability(id),
    refetchInterval: 10000,
  });
  const list = useQuery({
    queryKey: ["participants", id, offset, token],
    queryFn: () => listRegistrations(id, token, offset),
    refetchInterval: 10000,
  });
  return (
    <main className="workspace">
      <Link className="breadcrumb" to="/organizer">
        <Icon name="back" />
        Панель организатора
      </Link>
      <div className="page-heading">
        <div>
          <h1>{event.data?.title || "Участники мероприятия"}</h1>
          <p className="intro">
            Регистрации, очередь и посещаемость — в реальном времени.
          </p>
        </div>
        <Link className="button" to={`/organizer/events/${id}/check-in`}>
          <Icon name="ticket" />
          Проверка билетов и check-in
        </Link>
      </div>
      <nav className="workspace-nav" aria-label="Управление мероприятием">
        <span className="active">Участники</span>
        <Link to={`/organizer/events/${id}/edit`}>
          Редактировать мероприятие
        </Link>
        <Link to={`/events/${id}`}>Публичная страница</Link>
      </nav>
      <ErrorMessage error={event.error} />
      <ErrorMessage error={availability.error} />
      {availability.isPending && <Loading />}
      {availability.data && !availability.isError && (
        <dl className="stats">
          <div>
            <dt>Подтверждено</dt>
            <dd>
              {availability.data.confirmed}{" "}
              <small>/ {availability.data.capacity}</small>
            </dd>
          </div>
          <div>
            <dt>В очереди</dt>
            <dd>{availability.data.waiting}</dd>
          </div>
          <div>
            <dt>Прошли check-in</dt>
            <dd>{availability.data.checked_in}</dd>
          </div>
          <div>
            <dt>Свободных мест</dt>
            <dd>{availability.data.available}</dd>
          </div>
        </dl>
      )}
      {list.isPending && <Loading />}
      {list.isError && (
        <>
          <ErrorMessage error={list.error} />
          <button onClick={() => void list.refetch()}>Повторить</button>
        </>
      )}
      {list.data && !list.isError && (
        <section className="panel">
          <h2>Регистрации: {list.data.total}</h2>
          {list.data.items.length === 0 ? (
            <div className="empty-state">
              <Icon name="people" />
              <h3>Пока никто не зарегистрировался.</h3>
              <p>
                Поделитесь публичной страницей события с будущими участниками.
              </p>
              <Link className="text-link" to={`/events/${id}`}>
                Открыть публичную страницу <Icon name="arrow" />
              </Link>
            </div>
          ) : (
            <div className="table-scroll">
              <table
                className="participants-table"
                role="table"
                aria-label="Список участников"
              >
                <thead>
                  <tr>
                    <th scope="col">Email</th>
                    <th scope="col">Статус</th>
                    <th scope="col">Место в очереди</th>
                    <th scope="col">Check-in</th>
                  </tr>
                </thead>
                <tbody>
                  {list.data.items.map((record) => (
                    <tr key={record.id}>
                      <td>
                        <span className="mobile-cell-label" aria-hidden="true">
                          Email
                        </span>
                        {record.email}
                      </td>
                      <td>
                        <span className="mobile-cell-label" aria-hidden="true">
                          Статус
                        </span>
                        <span className={`status-pill ${record.status}`}>
                          {registrationLabels[record.status]}
                        </span>
                      </td>
                      <td>
                        <span className="mobile-cell-label" aria-hidden="true">
                          Место в очереди
                        </span>
                        {record.queue_position ?? "—"}
                      </td>
                      <td>
                        <span className="mobile-cell-label" aria-hidden="true">
                          Check-in
                        </span>
                        {record.checked_in_at ? (
                          <span className="status">Вход отмечен</span>
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {(offset > 0 || list.data.total > 20) && (
            <nav className="pagination" aria-label="Страницы регистраций">
              <button
                className="secondary"
                disabled={!offset}
                onClick={() => setOffset(Math.max(0, offset - 20))}
              >
                Назад
              </button>
              <span>Страница {Math.floor(offset / 20) + 1}</span>
              <button
                className="secondary"
                disabled={offset + 20 >= list.data.total}
                onClick={() => setOffset(offset + 20)}
              >
                Далее
              </button>
            </nav>
          )}
        </section>
      )}
      <p className="footnote">
        Список и счётчики обновляются автоматически. Отменённые записи
        сохраняются в истории.
      </p>
    </main>
  );
}

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useLocation, useParams } from "react-router-dom";
import {
  changeParticipation,
  getAvailability,
  getRegistration,
  registrationLabels,
} from "../api/registrations";
import { getTicket } from "../api/tickets";
import { getEvent } from "../api/events";
import { formatDate } from "../lib/dates";
import { tokenFromHash } from "../lib/registrationSecrets";
import { ErrorMessage, Loading } from "../components/Feedback";
import { Brand } from "../components/Brand";
import { DateBlock } from "../components/EventVisual";
import { Icon } from "../components/Icon";

export function RegistrationStatus() {
  const { id = "" } = useParams();
  const token = tokenFromHash(useLocation().hash);
  const client = useQueryClient();
  const [confirmCancel, setConfirmCancel] = useState(false);
  const [copyStatus, setCopyStatus] = useState("");
  const [codeStatus, setCodeStatus] = useState("");
  const queryKey = ["registration", id, token];
  const query = useQuery({
    queryKey,
    queryFn: () => getRegistration(id, token),
    enabled: !!token,
    retry: false,
    refetchInterval: token ? 10000 : false,
  });
  const ticket = useQuery({
    queryKey: ["ticket", id, token],
    queryFn: () => getTicket(id, token),
    enabled: !!token && !!query.data,
    retry: false,
    refetchInterval: 10000,
  });
  const eventId = query.data?.event_id || "";
  const event = useQuery({
    queryKey: ["event", eventId],
    queryFn: () => getEvent(eventId),
    enabled: !!eventId,
    refetchInterval: 10000,
  });
  const availability = useQuery({
    queryKey: ["availability", eventId],
    queryFn: () => getAvailability(eventId),
    enabled: !!eventId,
    refetchInterval: eventId ? 10000 : false,
  });
  const used = !!(query.data?.checked_in_at || ticket.data?.checked_in_at);
  const change = useMutation({
    mutationFn: (action: "cancel" | "rejoin") =>
      changeParticipation(id, token, action),
    onSuccess: async (record) => {
      client.setQueryData(queryKey, record);
      setConfirmCancel(false);
      await Promise.all([
        client.invalidateQueries({
          queryKey: ["availability", record.event_id],
        }),
        client.invalidateQueries({ queryKey: ["events"] }),
        client.invalidateQueries({ queryKey: ["ticket", id, token] }),
      ]);
    },
  });
  async function copy(text: string, kind: "link" | "code") {
    try {
      await navigator.clipboard.writeText(text);
      if (kind === "link") setCopyStatus("Ссылка скопирована");
      else setCodeStatus("Код скопирован");
    } catch {
      if (kind === "link") setCopyStatus("Скопируйте ссылку из поля ниже.");
      else setCodeStatus("Выделите и скопируйте код билета.");
    }
  }
  return (
    <main className="status-layout">
      <Link className="breadcrumb" to="/">
        <Icon name="back" />
        Все мероприятия
      </Link>
      <h1>Ваше участие</h1>
      {!token ? (
        <section className="empty-state">
          <Icon name="lock" />
          <p role="alert" className="error">
            Откройте полную личную ссылку, которую вы получили после
            регистрации.
          </p>
          <p>
            Билет приходит по email. Для статуса, очереди и отмены нужна
            сохранённая личная ссылка.
          </p>
        </section>
      ) : (
        <>
          {query.isPending && <Loading />}
          {query.isError && (
            <section className="empty-state">
              <ErrorMessage error={query.error} />
              <button onClick={() => void query.refetch()}>Повторить</button>
            </section>
          )}
          {query.data && !query.isError && (
            <>
              <div className="participation-heading">
                <Icon
                  name={
                    query.data.status === "confirmed"
                      ? "check"
                      : query.data.status === "waiting"
                        ? "clock"
                        : "close"
                  }
                />
                <div>
                  <h2 role="status">{registrationLabels[query.data.status]}</h2>
                  <p>{query.data.email}</p>
                </div>
              </div>
              {query.data.status === "waiting" && (
                <section className="notice">
                  <div>
                    <h3>Ваше место в очереди: {query.data.queue_position}</h3>
                    <p>
                      Если место освободится, мы автоматически подтвердим
                      участие и отправим билет по email. Статус обновится здесь.
                    </p>
                  </div>
                </section>
              )}
              {query.data.status === "cancelled" && (
                <p className="intro">
                  Участие отменено. Ранее выданный билет больше не действует.
                  Если регистрация открыта, можно присоединиться снова.
                </p>
              )}
              {query.data.status === "confirmed" && (
                <section aria-label="Ваш билет">
                  <h2 className="visually-hidden">Ваш билет</h2>
                  {ticket.isPending && <Loading />}
                  <ErrorMessage error={ticket.error} />
                  {ticket.isError && (
                    <button onClick={() => void ticket.refetch()}>
                      Повторить загрузку билета
                    </button>
                  )}
                  {!ticket.isError && ticket.data && (
                    <>
                      <article className="ticket-paper">
                        <div className="ticket-top">
                          <Brand />
                          <span className="status-pill">
                            {used ? "Вход отмечен" : "Билет действителен"}
                          </span>
                        </div>
                        <div className="ticket-main">
                          <div>
                            <h3>
                              {event.data?.title || "Билет на мероприятие"}
                            </h3>
                            {event.data && (
                              <p>
                                <Icon name="calendar" />{" "}
                                {formatDate(event.data.starts_at)}
                              </p>
                            )}
                            <p>
                              <Icon name="mail" /> {query.data.email}
                            </p>
                            {ticket.data.checked_in_at && (
                              <p role="status" className="status">
                                Вход отмечен:{" "}
                                {formatDate(ticket.data.checked_in_at)}
                              </p>
                            )}
                          </div>
                          {event.data && (
                            <DateBlock date={event.data.starts_at} />
                          )}
                        </div>
                        <div className="ticket-bottom">
                          <div>
                            <h4>Код для проверки на входе</h4>
                            <p className="ticket-code">
                              {ticket.data.code.match(/.{1,4}/g)?.join(" ")}
                            </p>
                          </div>
                          <button
                            className="icon-button"
                            aria-label="Скопировать код билета"
                            onClick={() => void copy(ticket.data!.code, "code")}
                          >
                            <Icon name="copy" />
                          </button>
                        </div>
                      </article>
                      <p className="ticket-help" role="status">
                        {codeStatus ||
                          "Покажите код организатору при входе. Один билет — один check-in. Не публикуйте код и личную ссылку."}
                      </p>
                    </>
                  )}
                  {ticket.isSuccess && !ticket.data && (
                    <p>
                      Билет пока недоступен. Статус обновится автоматически.
                    </p>
                  )}
                </section>
              )}
              <p>
                <Link className="text-link" to={`/events/${eventId}`}>
                  Открыть мероприятие <Icon name="arrow" />
                </Link>
              </p>
              <ErrorMessage error={event.error} />
              <section className="manage-link">
                <h2>Сохраните вашу личную ссылку</h2>
                <p>
                  Это доступ к статусу, очереди и отмене участия. Аккаунт для
                  этого не нужен. Если потеряете код билета, найдите его в
                  письме или откройте эту страницу. Восстановление личной
                  ссылки по email пока недоступно.
                </p>
                <div className="form manage-link-row">
                  <label>
                    Личная ссылка управления
                    <input
                      readOnly
                      value={window.location.href}
                      onFocus={(e) => e.target.select()}
                    />
                  </label>
                  <button
                    className="secondary"
                    onClick={() => void copy(window.location.href, "link")}
                  >
                    <Icon name="copy" />
                    Скопировать ссылку
                  </button>
                </div>
                <p className="footnote" role="status">
                  {copyStatus ||
                    "Добавьте страницу в закладки. Не передавайте ссылку другим людям."}
                </p>
              </section>
              <div className="participation-actions">
                <ErrorMessage error={change.error} />
                {used && <p>После check-in отменить участие нельзя.</p>}
                {availability.data?.registration_open &&
                  !used &&
                  (query.data.status === "cancelled" ? (
                    <button
                      disabled={change.isPending}
                      onClick={() => change.mutate("rejoin")}
                    >
                      {change.isPending
                        ? "Возвращаем…"
                        : "Зарегистрироваться снова"}
                    </button>
                  ) : confirmCancel ? (
                    <div role="group" aria-label="Подтверждение отмены">
                      <p>
                        Отменить участие? Освободившееся место получит первый
                        ожидающий.
                      </p>
                      <button
                        className="danger"
                        disabled={change.isPending}
                        onClick={() => change.mutate("cancel")}
                      >
                        Да, отменить участие
                      </button>
                      <button
                        className="secondary"
                        disabled={change.isPending}
                        onClick={() => setConfirmCancel(false)}
                      >
                        Оставить участие
                      </button>
                    </div>
                  ) : (
                    <button
                      className="secondary"
                      onClick={() => setConfirmCancel(true)}
                    >
                      Отменить участие
                    </button>
                  ))}
                {availability.data && !availability.data.registration_open && (
                  <p className="muted">
                    Мероприятие началось. Изменение участия закрыто.
                  </p>
                )}
                <ErrorMessage error={availability.error} />
                <p className="footnote">
                  Статус обновляется автоматически. Билет и напоминания
                  отправляются по email.
                </p>
              </div>
            </>
          )}
        </>
      )}
    </main>
  );
}

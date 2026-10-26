import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { getAvailability, registerForEvent } from "../api/registrations";
import {
  newRegistrationToken,
  pendingAttempt,
  registrationPath,
  rememberAttempt,
} from "../lib/registrationSecrets";
import type { RegistrationAttempt } from "../lib/registrationSecrets";
import { ErrorMessage, Loading } from "./Feedback";
import { Icon } from "./Icon";

export function EventRegistration({ eventId }: { eventId: string }) {
  const [attempt, setAttempt] = useState<RegistrationAttempt | null>(() =>
    pendingAttempt(eventId),
  );
  const [email, setEmail] = useState(attempt?.email || "");
  const navigate = useNavigate();
  const availability = useQuery({
    queryKey: ["availability", eventId],
    queryFn: () => getAvailability(eventId),
    refetchInterval: 10000,
  });
  const registration = useMutation({
    mutationFn: (data: RegistrationAttempt) =>
      registerForEvent(eventId, data.email, data.token),
    onSuccess: (record, data) => {
      rememberAttempt(eventId, null);
      navigate(registrationPath(record.id, data.token));
    },
  });
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = email.trim().toLowerCase();
    const data =
      attempt?.email === normalized
        ? attempt
        : { email: normalized, token: newRegistrationToken() };
    setAttempt(data);
    rememberAttempt(eventId, data);
    registration.mutate(data);
  }
  return (
    <aside className="registration-card" aria-labelledby="registration-title">
      <h2 id="registration-title">Ваше место на событии</h2>
      <p className="intro">Один email — и вы на шаг ближе к встрече.</p>
      {availability.isPending && <Loading />}
      {availability.isError && (
        <>
          <ErrorMessage error={availability.error} />
          <button onClick={() => void availability.refetch()}>
            Повторить проверку мест
          </button>
        </>
      )}
      {availability.data && !availability.isError && (
        <>
          <span
            className={`status-pill ${availability.data.available ? "" : "waiting"}`}
          >
            {!availability.data.registration_open
              ? "Регистрация закрыта"
              : availability.data.available
                ? "Регистрация открыта"
                : "Есть лист ожидания"}
          </span>
          <dl className="event-meta">
            <div>
              <dt>Свободных мест</dt>
              <dd>
                {availability.data.available}{" "}
                <span className="muted">из {availability.data.capacity}</span>
              </dd>
            </div>
            <div>
              <dt>В очереди</dt>
              <dd>{availability.data.waiting}</dd>
            </div>
          </dl>
          {availability.data.registration_open ? (
            <form className="form" onSubmit={submit}>
              <label>
                Email для вашего билета
                <input
                  type="email"
                  required
                  maxLength={254}
                  autoComplete="email"
                  placeholder="you@example.com"
                  disabled={registration.isPending}
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
              </label>
              {!availability.data.available && (
                <p className="footnote">
                  Все места заняты. Встаньте в очередь — если место освободится,
                  мы автоматически подтвердим участие.
                </p>
              )}
              <ErrorMessage error={registration.error} />
              <button disabled={registration.isPending}>
                {registration.isPending ? (
                  "Регистрируем…"
                ) : availability.data.available ? (
                  <>
                    <Icon name="ticket" />
                    Зарегистрироваться
                  </>
                ) : (
                  "Встать в очередь"
                )}
              </button>
              <p className="footnote">
                Билет придёт по email после подтверждения места. Личная ссылка
                для статуса и отмены появится на следующем экране — сохраните
                её.
              </p>
            </form>
          ) : (
            <p role="status" className="muted">
              Мероприятие уже началось. Регистрация закрыта.
            </p>
          )}
          <div className="registration-reassurance">
            <Icon name="lock" />
            Без создания аккаунта. Вход по билету.
          </div>
        </>
      )}
    </aside>
  );
}

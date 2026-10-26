import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { checkIn, verifyTicket } from "../api/tickets";
import { getEvent } from "../api/events";
import { ErrorMessage, Loading } from "../components/Feedback";
import { formatDate } from "../lib/dates";
import { Icon } from "../components/Icon";

export function TicketCheckIn({ token }: { token: string }) {
  const { id = "" } = useParams();
  const [code, setCode] = useState("");
  const client = useQueryClient();
  const event = useQuery({
    queryKey: ["event", id],
    queryFn: () => getEvent(id),
    refetchInterval: 10000,
  });
  const verify = useMutation({
    mutationFn: () => verifyTicket(id, code, token),
  });
  const admission = useMutation({
    mutationFn: () => checkIn(id, code, token),
    onError: () => verify.reset(),
    onSuccess: async () => {
      await Promise.all([
        client.invalidateQueries({ queryKey: ["availability", id] }),
        client.invalidateQueries({ queryKey: ["participants", id] }),
      ]);
    },
  });
  const result = admission.data?.ticket || verify.data;
  const busy = verify.isPending || admission.isPending;
  return (
    <main className="narrow checkin-layout">
      <Link className="breadcrumb" to={`/organizer/events/${id}/participants`}>
        <Icon name="back" />
        Участники и статистика
      </Link>
      <h1>Проверка билетов</h1>
      <p>{event.data?.title}</p>
      {event.isPending && <Loading />}
      {event.isError && (
        <>
          <ErrorMessage error={event.error} />
          <button onClick={() => void event.refetch()}>Повторить</button>
        </>
      )}
      {event.data && !event.isError && (
        <>
          <form
            className="panel form"
            onSubmit={(e) => {
              e.preventDefault();
              admission.reset();
              verify.mutate();
            }}
          >
            <label>
              Код билета
              <input
                required
                maxLength={256}
                autoComplete="off"
                spellCheck={false}
                value={code}
                disabled={busy}
                onChange={(e) => {
                  setCode(e.target.value);
                  verify.reset();
                  admission.reset();
                }}
                placeholder="32 символа с билета участника"
              />
            </label>
            <button disabled={busy || !code.trim()}>
              {verify.isPending ? "Проверяем…" : "Проверить билет"}
            </button>
            <ErrorMessage error={verify.error || admission.error} />
            {result && (
              <div className="checkin-result" role="status">
                <p>{result.email}</p>
                <p>
                  {result.status === "valid"
                    ? "Билет действителен"
                    : result.status === "revoked"
                      ? "Билет отозван"
                      : "Вход уже зарегистрирован"}
                </p>
                {result.checked_in_at && (
                  <p>Check-in: {formatDate(result.checked_in_at)}</p>
                )}
                {admission.data && (
                  <p>
                    {admission.data.already_checked_in
                      ? "Повторный вход не засчитан."
                      : "Check-in выполнен."}
                  </p>
                )}
                {result.status === "valid" && !admission.isError && (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => admission.mutate()}
                  >
                    {admission.isPending ? "Сохраняем…" : "Подтвердить вход"}
                  </button>
                )}
              </div>
            )}
            <p className="footnote">
              Проверка не отмечает посещение. Вход фиксируется кнопкой
              «Подтвердить вход». При потере ответа проверьте тот же код снова.
            </p>
          </form>
        </>
      )}
    </main>
  );
}

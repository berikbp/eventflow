import type { Event } from "../api/events";
import { Icon } from "./Icon";

export function DateBlock({ date }: { date: string }) {
  const value = new Date(date);
  return (
    <span className="date-block" aria-label={value.toLocaleDateString("ru-RU")}>
      <strong>{value.getDate().toString().padStart(2, "0")}</strong>
      <span>
        {value.toLocaleDateString("ru-RU", { month: "short" }).replace(".", "")}
      </span>
    </span>
  );
}

export function EventVisual({
  event,
  detail = false,
}: {
  event: Event;
  detail?: boolean;
}) {
  const demo =
    event.id === "00000000-0000-4000-8000-000000000001" ||
    event.id === "00000000-0000-4000-8000-000000000002";
  const workshop = event.id.endsWith("000002");
  return (
    <div
      className={`event-visual ${detail ? "event-visual-detail" : ""} ${workshop ? "visual-workshop" : "visual-meetup"} ${!demo ? "visual-poster" : ""}`}
    >
      {demo ? (
        <img
          src={`/assets/photos/${workshop ? "workshop" : "community"}.jpg`}
          alt=""
          loading={detail ? "eager" : "lazy"}
        />
      ) : (
        <div className="poster-type">
          <Icon name="ticket" />
          <span>{event.title}</span>
          <small>eventflow</small>
        </div>
      )}
      <DateBlock date={event.starts_at} />
      {demo && <span className="visual-caption">Иллюстрация встречи</span>}
    </div>
  );
}

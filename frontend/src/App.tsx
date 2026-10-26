import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, NavLink, Route, Routes } from "react-router-dom";
import { checkHealth } from "./api/health";
import { OrganizerAccess } from "./components/OrganizerAccess";
import { EventList } from "./pages/EventList";
import { EventDetail } from "./pages/EventDetail";
import { EventEditor } from "./pages/EventEditor";
import { RegistrationStatus } from "./pages/RegistrationStatus";
import { TicketCheckIn } from "./pages/TicketCheckIn";
import { RealtimeStatus } from "./components/RealtimeStatus";
import { EventParticipants } from "./pages/EventParticipants";
import { Icon } from "./components/Icon";
import { Brand } from "./components/Brand";

function Foundation() {
  const health = useQuery({
    queryKey: ["readiness"],
    queryFn: checkHealth,
    retry: 1,
    refetchInterval: 15000,
  });
  return (
    <main className="narrow">
      <Link className="breadcrumb" to="/">
        <Icon name="back" />
        Все мероприятия
      </Link>
      <h1>Состояние сервиса</h1>
      <p className="intro">Проверка доступности EventFlow.</p>
      <section className="status-card">
        <h2>API и база данных</h2>
        <p role="status" className={health.isError ? "error" : "status"}>
          {health.isPending
            ? "Проверяем подключение…"
            : health.isError
              ? health.error.message
              : "API отвечает · PostgreSQL подключён"}
        </p>
        <button
          disabled={health.isFetching}
          onClick={() => void health.refetch()}
        >
          {health.isFetching ? "Проверяем…" : "Проверить снова"}
        </button>
      </section>
      <p className="footnote">Проверка выполняется каждые 15 секунд.</p>
    </main>
  );
}

export default function App() {
  const [token, setToken] = useState("");
  return (
    <>
      <a className="skip-link" href="#main-content">
        Перейти к содержимому
      </a>
      <header
        className={`site-header page-width ${token ? "is-authenticated" : ""}`}
      >
        <Brand />
        <nav className="site-nav" aria-label="Главная навигация">
          <NavLink to="/" end>
            Афиша
          </NavLink>
          <a href="/#how-it-works">Как это работает</a>
        </nav>
        <div className="header-actions">
          {token && (
            <button className="secondary" onClick={() => setToken("")}>
              Выйти
            </button>
          )}
          <Link className="button button-ghost" to="/organizer">
            {token ? "Мои мероприятия" : "Организатору"}
            <Icon name="arrow" />
          </Link>
        </div>
      </header>
      <div id="main-content" tabIndex={-1}>
        <Routes>
          <Route path="/" element={<EventList />} />
          <Route path="/events/:id" element={<EventDetail token={token} />} />
          <Route path="/registrations/:id" element={<RegistrationStatus />} />
          <Route
            path="/organizer"
            element={
              <OrganizerAccess token={token} onToken={setToken}>
                <EventList manage />
              </OrganizerAccess>
            }
          />
          <Route
            path="/organizer/events/new"
            element={
              <OrganizerAccess token={token} onToken={setToken}>
                <EventEditor token={token} />
              </OrganizerAccess>
            }
          />
          <Route
            path="/organizer/events/:id/edit"
            element={
              <OrganizerAccess token={token} onToken={setToken}>
                <EventEditor token={token} />
              </OrganizerAccess>
            }
          />
          <Route
            path="/organizer/events/:id/participants"
            element={
              <OrganizerAccess token={token} onToken={setToken}>
                <EventParticipants token={token} />
              </OrganizerAccess>
            }
          />
          <Route
            path="/organizer/events/:id/check-in"
            element={
              <OrganizerAccess token={token} onToken={setToken}>
                <TicketCheckIn token={token} />
              </OrganizerAccess>
            }
          />
          <Route path="/system" element={<Foundation />} />
          <Route
            path="*"
            element={
              <main className="narrow">
                <section className="empty-state">
                  <Icon name="search" />
                  <h1>Страница не найдена</h1>
                  <p>
                    Возможно, ссылка устарела. Найдите свою следующую встречу в
                    афише.
                  </p>
                  <Link className="button" to="/">
                    На главную <Icon name="arrow" />
                  </Link>
                </section>
              </main>
            }
          />
        </Routes>
      </div>
      <footer className="site-footer">
        <div className="page-width">
          <div className="footer-top">
            <div>
              <Brand />
              <p>
                Больше встреч. Больше своего.
                <br />
                Находите события и людей, с которыми хочется быть рядом.
              </p>
            </div>
            <div className="footer-links">
              <div>
                <strong>Участникам</strong>
                <Link to="/">Афиша мероприятий</Link>
                <a href="/#how-it-works">Как получить билет</a>
              </div>
              <div>
                <strong>Организаторам</strong>
                <Link to="/organizer/events/new">Создать мероприятие</Link>
                <Link to="/organizer">Панель организатора</Link>
              </div>
            </div>
          </div>
          <div className="footer-bottom">
            <span>EventFlow · События сближают.</span>
            <RealtimeStatus />
            <Link to="/system">Состояние сервиса</Link>
          </div>
        </div>
      </footer>
    </>
  );
}

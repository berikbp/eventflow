import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, Route, Routes } from 'react-router-dom'
import { checkHealth } from './api/health'
import { OrganizerAccess } from './components/OrganizerAccess'
import { EventList } from './pages/EventList'
import { EventDetail } from './pages/EventDetail'
import { EventEditor } from './pages/EventEditor'
import { RegistrationStatus } from './pages/RegistrationStatus'
import { EventParticipants } from './pages/EventParticipants'

function Foundation() {
  const health = useQuery({ queryKey: ['readiness'], queryFn: checkHealth, retry: 1, refetchInterval: 15000 })
  return (
    <main>
      <span className="eyebrow">СОСТОЯНИЕ СИСТЕМЫ</span>
      <h1>Мероприятия начинаются<br />с надёжной основы.</h1>
      <p className="intro">Проверка доступности API и базы данных EventFlow.</p>
      <section aria-labelledby="status-title" className="status-card">
        <div><span className="eyebrow">СОСТОЯНИЕ СИСТЕМЫ</span><h2 id="status-title">Подключение к API и PostgreSQL</h2></div>
        <p role="status" className={health.isError ? 'error' : 'status'}>
          {health.isPending ? 'Проверяем подключение…' : health.isError ? health.error.message : 'API отвечает · PostgreSQL подключён'}
        </p>
        <button disabled={health.isFetching} onClick={() => void health.refetch()}>{health.isFetching ? 'Проверяем…' : 'Проверить снова'}</button>
      </section>
      <p className="footnote">Проверка обновляется каждые 15 секунд. Это техническая проверка доступности, а не real-time статистика мероприятий.</p>
    </main>
  )
}

export default function App() {
  const [token, setToken] = useState('')
  return <>
    <header><Link to="/" className="brand">eventflow<span>↗</span></Link>
      <nav aria-label="Главная навигация"><Link to="/">Мероприятия</Link><Link to="/organizer">Организатору</Link><Link to="/system">Статус</Link>{token && <button className="secondary" onClick={() => setToken('')}>Выйти</button>}</nav>
    </header>
    <Routes>
      <Route path="/" element={<EventList />} />
      <Route path="/events/:id" element={<EventDetail token={token} />} />
      <Route path="/registrations/:id" element={<RegistrationStatus />} />
      <Route path="/organizer" element={<OrganizerAccess token={token} onToken={setToken}><EventList manage /></OrganizerAccess>} />
      <Route path="/organizer/events/new" element={<OrganizerAccess token={token} onToken={setToken}><EventEditor token={token} /></OrganizerAccess>} />
      <Route path="/organizer/events/:id/edit" element={<OrganizerAccess token={token} onToken={setToken}><EventEditor token={token} /></OrganizerAccess>} />
      <Route path="/organizer/events/:id/participants" element={<OrganizerAccess token={token} onToken={setToken}><EventParticipants token={token} /></OrganizerAccess>} />
      <Route path="/system" element={<Foundation />} />
      <Route path="*" element={<main><h1>Страница не найдена</h1><Link to="/">На главную</Link></main>} />
    </Routes>
  </>
}

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useLocation } from 'react-router-dom'
import { listEvents } from '../api/events'
import { formatDate } from '../lib/dates'
import { ErrorMessage, Loading } from '../components/Feedback'

export function EventList({ manage = false }: { manage?: boolean }) {
  const [offset, setOffset] = useState(0)
  const location = useLocation()
  const query = useQuery({ queryKey: ['events', offset], queryFn: () => listEvents(offset), refetchInterval: 10000 })
  return <main>
    <div className="page-heading"><div><span className="eyebrow">{manage ? 'ПАНЕЛЬ ОРГАНИЗАТОРА' : 'ВСТРЕЧАЙТЕСЬ. УЗНАВАЙТЕ. УЧАСТВУЙТЕ.'}</span>
      <h1>{manage ? 'Ваши мероприятия' : 'Найдите свою встречу'}</h1>
      <p className="intro">{manage ? 'Создавайте мероприятия и управляйте расписанием.' : 'Ближайшие события и новые возможности для общения.'}</p>
    </div>{manage && <Link className="button" to="/organizer/events/new">+ Создать мероприятие</Link>}</div>
    {location.state?.notice && <p className="status" role="status">{location.state.notice}</p>}
    {query.isPending && <Loading />}
    {query.isError && <div><ErrorMessage error={query.error} /><button onClick={() => void query.refetch()}>Повторить</button></div>}
    {query.data && !query.isError && <>
      <p className="muted">Всего мероприятий: {query.data.total}</p>
      {query.data.items.length === 0 ? <section className="panel empty"><h2>{offset ? 'Здесь пока пусто' : 'Мероприятий пока нет'}</h2><p>{manage ? 'Создайте первое мероприятие — оно появится в общем списке.' : 'Загляните позже: новые встречи скоро появятся здесь.'}</p></section> :
        <div className="event-grid">{query.data.items.map(event => <article key={event.id} className="panel event-card">
          <span className="eyebrow">МЕРОПРИЯТИЕ</span>
          <h2><Link to={manage ? `/organizer/events/${event.id}/edit` : `/events/${event.id}`}>{event.title}</Link></h2>
          <time dateTime={event.starts_at}>{formatDate(event.starts_at)}</time>
          <p className="preview">{event.description || 'Описание пока не добавлено.'}</p>
          <div className="card-footer"><span>Вместимость: {event.capacity}</span><Link to={manage ? `/organizer/events/${event.id}/participants` : `/events/${event.id}`}>{manage ? 'Участники ↗' : 'Подробнее ↗'}</Link></div>
        </article>)}</div>}
      <nav className="pagination" aria-label="Страницы мероприятий">
        <button className="secondary" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 20))}>Назад</button>
        <span>Страница {Math.floor(offset / 20) + 1}</span>
        <button className="secondary" disabled={offset + 20 >= query.data.total} onClick={() => setOffset(offset + 20)}>Далее</button>
      </nav>
      <p className="footnote">Время указано в часовом поясе вашего устройства.</p>
    </>}
  </main>
}

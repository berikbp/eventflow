import { useQuery } from '@tanstack/react-query'
import { Link, useLocation, useParams } from 'react-router-dom'
import { getEvent } from '../api/events'
import { formatDate } from '../lib/dates'
import { ErrorMessage, Loading } from '../components/Feedback'

export function EventDetail({ token }: { token: string }) {
  const { id = '' } = useParams()
  const location = useLocation()
  const query = useQuery({ queryKey: ['event', id], queryFn: () => getEvent(id) })
  return <main className="narrow">
    <Link to="/">← Все мероприятия</Link>
    {query.isPending && <Loading />}
    {query.isError && <><ErrorMessage error={query.error} /><button onClick={() => void query.refetch()}>Повторить</button></>}
    {query.data && <>
      {location.state?.notice && <p role="status" className="status">{location.state.notice}</p>}
      <h1>{query.data.title}</h1>
      <section className="panel"><dl className="event-meta"><div><dt>Дата и время</dt><dd><time dateTime={query.data.starts_at}>{formatDate(query.data.starts_at)}</time></dd></div><div><dt>Вместимость</dt><dd>{query.data.capacity} участников</dd></div></dl>
        <p className="description">{query.data.description || 'Описание пока не добавлено.'}</p>
        <p className="footnote">Время указано в часовом поясе вашего устройства.</p>
      </section>
      <p className="intro">Онлайн-регистрация пока недоступна.</p>
      {token && <Link className="button" to={`/organizer/events/${id}/edit`}>Редактировать мероприятие</Link>}
    </>}
  </main>
}

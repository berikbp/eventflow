import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { getAvailability, listRegistrations, registrationLabels } from '../api/registrations'
import { getEvent } from '../api/events'
import { ErrorMessage, Loading } from '../components/Feedback'

export function EventParticipants({ token }: { token: string }) {
  const { id = '' } = useParams()
  const [offset, setOffset] = useState(0)
  const event = useQuery({ queryKey: ['event', id], queryFn: () => getEvent(id) })
  const availability = useQuery({ queryKey: ['availability', id], queryFn: () => getAvailability(id), refetchInterval: 10000 })
  const list = useQuery({
    queryKey: ['participants', id, offset, token],
    queryFn: () => listRegistrations(id, token, offset), refetchInterval: 10000,
  })
  return <main>
    <Link to="/organizer">← Панель организатора</Link>
    <h1>{event.data?.title || 'Участники мероприятия'}</h1>
    <p><Link to={`/organizer/events/${id}/check-in`}>Проверка билетов и check-in</Link> · <Link to={`/organizer/events/${id}/edit`}>Редактировать мероприятие</Link> · <Link to={`/events/${id}`}>Публичная страница</Link></p>
    <ErrorMessage error={event.error} /><ErrorMessage error={availability.error} />
    {availability.data && <dl className="panel event-meta">
      <div><dt>Подтверждено</dt><dd>{availability.data.confirmed} / {availability.data.capacity}</dd></div>
      <div><dt>Прошли check-in</dt><dd>{availability.data.checked_in}</dd></div>
      <div><dt>В очереди</dt><dd>{availability.data.waiting}</dd></div>
      <div><dt>Свободных мест</dt><dd>{availability.data.available}</dd></div>
    </dl>}
    {list.isPending && <Loading />}
    {list.isError && <><ErrorMessage error={list.error} /><button onClick={() => void list.refetch()}>Повторить</button></>}
    {list.data && !list.isError && <section className="panel">
      <h2>Регистрации: {list.data.total}</h2>
      {list.data.items.length === 0 ? <p className="muted">Пока никто не зарегистрировался.</p> : <div className="table-scroll"><table>
        <thead><tr><th>Email</th><th>Статус</th><th>Место в очереди</th><th>Check-in</th></tr></thead>
        <tbody>{list.data.items.map(record => <tr key={record.id}><td>{record.email}</td><td>{registrationLabels[record.status]}</td><td>{record.queue_position ?? '—'}</td><td>{record.checked_in_at ? 'Вход отмечен' : '—'}</td></tr>)}</tbody>
      </table></div>}
      <nav className="pagination" aria-label="Страницы регистраций"><button className="secondary" disabled={!offset} onClick={() => setOffset(Math.max(0, offset - 20))}>Назад</button><span>Страница {Math.floor(offset / 20) + 1}</span><button className="secondary" disabled={offset + 20 >= list.data.total} onClick={() => setOffset(offset + 20)}>Далее</button></nav>
    </section>}
    <p className="footnote">Список и счётчики проверяются каждые 10 секунд. Отменённые записи сохраняются в истории.</p>
  </main>
}

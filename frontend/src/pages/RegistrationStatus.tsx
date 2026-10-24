import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useLocation, useParams } from 'react-router-dom'
import { changeParticipation, getAvailability, getRegistration, registrationLabels } from '../api/registrations'
import { getTicket } from '../api/tickets'
import { formatDate } from '../lib/dates'
import { tokenFromHash } from '../lib/registrationSecrets'
import { ErrorMessage, Loading } from '../components/Feedback'

export function RegistrationStatus() {
  const { id = '' } = useParams()
  const location = useLocation()
  const token = tokenFromHash(location.hash)
  const client = useQueryClient()
  const [confirmCancel, setConfirmCancel] = useState(false)
  const [copyStatus, setCopyStatus] = useState('')
  const queryKey = ['registration', id, token]
  const query = useQuery({
    queryKey, queryFn: () => getRegistration(id, token),
    enabled: !!token, retry: false, refetchInterval: token ? 10000 : false,
  })
  const ticket = useQuery({
    queryKey: ['ticket', id, token], queryFn: () => getTicket(id, token),
    enabled: !!token && !!query.data, retry: false, refetchInterval: 10000,
  })
  const eventId = query.data?.event_id || ''
  const availability = useQuery({
    queryKey: ['availability', eventId], queryFn: () => getAvailability(eventId),
    enabled: !!eventId, refetchInterval: eventId ? 10000 : false,
  })
  const change = useMutation({
    mutationFn: (action: 'cancel' | 'rejoin') => changeParticipation(id, token, action),
    onSuccess: async (record) => {
      client.setQueryData(queryKey, record)
      setConfirmCancel(false)
      await Promise.all([
        client.invalidateQueries({ queryKey: ['availability', record.event_id] }),
        client.invalidateQueries({ queryKey: ['events'] }),
        client.invalidateQueries({ queryKey: ['ticket', id, token] }),
      ])
    },
  })
  async function copyLink() {
    try { await navigator.clipboard.writeText(window.location.href); setCopyStatus('Ссылка скопирована') }
    catch { setCopyStatus('Не удалось скопировать автоматически. Скопируйте ссылку из поля ниже.') }
  }
  return <main className="narrow">
    <span className="eyebrow">МОЯ РЕГИСТРАЦИЯ</span>
    <h1>Ваше участие</h1>
    {!token ? <p role="alert" className="error">Откройте полную личную ссылку, которую вы получили после регистрации.</p> : <>
      {query.isPending && <Loading />}
      {query.isError && <><ErrorMessage error={query.error} /><button onClick={() => void query.refetch()}>Повторить</button></>}
      {query.data && !query.isError && <section className="panel">
        <h2 role="status" className={query.data.status === 'cancelled' ? 'muted' : 'status'}>{registrationLabels[query.data.status]}</h2>
        <p>{query.data.email}</p>
        {query.data.status === 'waiting' && <p>Место в очереди: <strong>{query.data.queue_position}</strong>. Если место освободится, статус обновится автоматически.</p>}
        {query.data.status === 'confirmed' && <section aria-label="Ваш билет">
          <h2>Ваш билет</h2>
          {ticket.isPending && <Loading />}
          <ErrorMessage error={ticket.error} />
          {ticket.isError && <button onClick={() => void ticket.refetch()}>Повторить загрузку билета</button>}
          {!ticket.isError && ticket.data && <>
            <p>Покажите код организатору при входе. Не публикуйте его.</p>
            <p className="ticket-code">{ticket.data.code.match(/.{1,4}/g)?.join(' ')}</p>
            {ticket.data.checked_in_at && <p role="status">Вход отмечен: {formatDate(ticket.data.checked_in_at)}</p>}
          </>}
          {ticket.isSuccess && !ticket.data && <p>Билет пока недоступен. Статус обновится автоматически.</p>}
        </section>}
        <p><Link to={`/events/${eventId}`}>Открыть мероприятие ↗</Link></p>
        <div className="form">
          <label>Личная ссылка управления<input readOnly value={window.location.href} onFocus={event => event.target.select()} /></label>
          <button className="secondary" onClick={() => void copyLink()}>Скопировать ссылку</button>
          <p className="footnote" role="status">{copyStatus || 'Сохраните ссылку в закладках. Она даёт доступ к вашей регистрации. Не публикуйте её.'}</p>
        </div>
        <ErrorMessage error={change.error} />
        {query.data.checked_in_at && <p>После check-in отменить участие нельзя.</p>}
        {availability.data?.registration_open && !query.data.checked_in_at && (query.data.status === 'cancelled' ?
          <button disabled={change.isPending} onClick={() => change.mutate('rejoin')}>{change.isPending ? 'Возвращаем…' : 'Зарегистрироваться снова'}</button> :
          confirmCancel ? <div role="group" aria-label="Подтверждение отмены"><p>Отменить участие? Освободившееся место получит первый ожидающий.</p><button className="danger" disabled={change.isPending} onClick={() => change.mutate('cancel')}>Да, отменить участие</button><button className="secondary" disabled={change.isPending} onClick={() => setConfirmCancel(false)}>Оставить участие</button></div> :
          <button className="danger" onClick={() => setConfirmCancel(true)}>Отменить участие</button>)}
        {availability.data && !availability.data.registration_open && <p className="muted">Мероприятие началось. Изменение участия закрыто.</p>}
        <ErrorMessage error={availability.error} />
        <p className="footnote">Статус обновляется автоматически. Билет и напоминания отправляются по email; сохраните личную ссылку управления.</p>
      </section>}
    </>}
    <p><Link to="/">← Все мероприятия</Link></p>
  </main>
}

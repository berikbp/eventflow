import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getAvailability, registerForEvent } from '../api/registrations'
import { newRegistrationToken, pendingAttempt, registrationPath, rememberAttempt } from '../lib/registrationSecrets'
import type { RegistrationAttempt } from '../lib/registrationSecrets'
import { ErrorMessage, Loading } from './Feedback'

export function EventRegistration({ eventId }: { eventId: string }) {
  const [attempt, setAttempt] = useState<RegistrationAttempt | null>(() => pendingAttempt(eventId))
  const [email, setEmail] = useState(attempt?.email || '')
  const navigate = useNavigate()
  const availability = useQuery({
    queryKey: ['availability', eventId], queryFn: () => getAvailability(eventId),
    refetchInterval: 10000,
  })
  const registration = useMutation({
    mutationFn: (data: RegistrationAttempt) => registerForEvent(eventId, data.email, data.token),
    onSuccess: (record, data) => {
      rememberAttempt(eventId, null)
      navigate(registrationPath(record.id, data.token))
    },
  })
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const normalized = email.trim().toLowerCase()
    const data = attempt?.email === normalized ? attempt : { email: normalized, token: newRegistrationToken() }
    setAttempt(data)
    rememberAttempt(eventId, data)
    registration.mutate(data)
  }
  return <section className="panel form" aria-labelledby="registration-title">
    <h2 id="registration-title">Присоединиться к мероприятию</h2>
    {availability.isPending && <Loading />}
    {availability.isError && <><ErrorMessage error={availability.error} /><button onClick={() => void availability.refetch()}>Повторить проверку мест</button></>}
    {availability.data && <>
      <dl className="event-meta">
        <div><dt>Свободных мест</dt><dd>{availability.data.available} из {availability.data.capacity}</dd></div>
        <div><dt>Участников</dt><dd>{availability.data.confirmed}</dd></div>
        <div><dt>В очереди</dt><dd>{availability.data.waiting}</dd></div>
      </dl>
      {availability.data.registration_open ? <form onSubmit={submit}>
        <p className="intro">{availability.data.available ? 'Оставьте email, чтобы зарегистрироваться.' : 'Все места заняты. Присоединитесь к очереди — при отмене участия место получит первый ожидающий.'}</p>
        <label>Email<input type="email" required maxLength={254} autoComplete="email" disabled={registration.isPending} value={email} onChange={event => setEmail(event.target.value)} /></label>
        <ErrorMessage error={registration.error} />
        <button disabled={registration.isPending}>{registration.isPending ? 'Регистрируем…' : availability.data.available ? 'Зарегистрироваться' : 'Встать в очередь'}</button>
        <p className="footnote">После регистрации сохраните личную ссылку: по ней можно проверить статус и отменить участие. Не передавайте её другим людям. Письма пока не отправляются.</p>
      </form> : <p role="status" className="muted">Мероприятие уже началось. Регистрация закрыта.</p>}
    </>}
  </section>
}

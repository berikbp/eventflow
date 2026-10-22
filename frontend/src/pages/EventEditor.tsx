import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { createEvent, updateEvent, deleteEvent, getEvent } from '../api/events'
import type { Event, EventInput } from '../api/events'
import { toLocalInput, toUtc } from '../lib/dates'
import { ErrorMessage, Loading } from '../components/Feedback'

function EditorForm({ event, token }: { event?: Event; token: string }) {
  const [title, setTitle] = useState(event?.title || '')
  const [description, setDescription] = useState(event?.description || '')
  const [date, setDate] = useState(event ? toLocalInput(event.starts_at) : '')
  const [capacity, setCapacity] = useState(String(event?.capacity || 30))
  const [formError, setFormError] = useState<Error | null>(null)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const navigate = useNavigate()
  const client = useQueryClient()
  const save = useMutation({
    mutationFn: (data: Partial<EventInput>) => event ? updateEvent(event.id, data, token) : createEvent(data as EventInput, token),
    onSuccess: async (saved) => {
      client.setQueryData(['event', saved.id], saved)
      await client.invalidateQueries({ queryKey: ['events'] })
      navigate(`/events/${saved.id}`, { state: { notice: event ? 'Изменения сохранены' : 'Мероприятие создано' } })
    },
  })
  const remove = useMutation({
    mutationFn: () => deleteEvent(event!.id, token),
    onSuccess: async () => {
      client.removeQueries({ queryKey: ['event', event!.id] })
      await client.invalidateQueries({ queryKey: ['events'] })
      navigate('/organizer', { state: { notice: 'Мероприятие удалено' } })
    },
  })
  const busy = save.isPending || remove.isPending
  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setFormError(null)
    try {
      const trimmed = title.trim()
      const count = Number(capacity)
      if (!trimmed) throw new Error('Укажите название мероприятия')
      if (!Number.isInteger(count) || count < 1 || count > 1000000) throw new Error('Вместимость должна быть целым числом от 1 до 1 000 000')
      const startsAt = toUtc(date)
      const dateChanged = !event || date !== toLocalInput(event.starts_at)
      if (dateChanged && new Date(startsAt) <= new Date()) throw new Error('Дата мероприятия должна быть в будущем')
      const data: Partial<EventInput> = { title: trimmed, description: description.trim(), capacity: count }
      if (dateChanged) data.starts_at = startsAt
      save.mutate(data)
    } catch (error) { setFormError(error instanceof Error ? error : new Error('Проверьте данные')) }
  }
  return <>
    <form className="panel form" onSubmit={submit}>
      <fieldset disabled={busy}>
        <label>Название<input required maxLength={200} value={title} onChange={e => setTitle(e.target.value)} /></label>
        <label>Описание<textarea rows={6} maxLength={10000} value={description} onChange={e => setDescription(e.target.value)} /></label>
        <div className="form-row"><label>Дата и время<input required type="datetime-local" value={date} onChange={e => setDate(e.target.value)} /></label>
          <label>Вместимость<input required type="number" min="1" max="1000000" step="1" value={capacity} onChange={e => setCapacity(e.target.value)} /></label></div>
        <p className="footnote">Время указано в часовом поясе устройства: {Intl.DateTimeFormat().resolvedOptions().timeZone}.</p>
        {event && <p className="footnote">Перенос пока сохраняет только дату. Автоматические уведомления ещё не подключены.</p>}
        <ErrorMessage error={formError || save.error} />
        <button disabled={busy}>{save.isPending ? 'Сохраняем…' : event ? 'Сохранить изменения' : 'Создать мероприятие'}</button>
      </fieldset>
    </form>
    {event && <section className="panel delete-panel"><h2>Удалить мероприятие</h2><p>Мероприятие исчезнет из списка. Восстановление не предусмотрено.</p>
      <ErrorMessage error={remove.error} />
      {confirmDelete ? <div role="group" aria-label="Подтверждение удаления"><p>Удалить «{event.title}»?</p><button className="danger" disabled={busy} onClick={() => remove.mutate()}>{remove.isPending ? 'Удаляем…' : 'Да, удалить'}</button><button className="secondary" disabled={busy} onClick={() => setConfirmDelete(false)}>Отмена</button></div> : <button className="danger" disabled={busy} onClick={() => setConfirmDelete(true)}>Удалить мероприятие</button>}
    </section>}
  </>
}

export function EventEditor({ token }: { token: string }) {
  const { id } = useParams()
  const query = useQuery({ queryKey: ['event', id], queryFn: () => getEvent(id!), enabled: !!id })
  return <main className="narrow">
    <Link to="/organizer">← Панель организатора</Link>
    <h1>{id ? 'Редактировать мероприятие' : 'Новая встреча'}</h1>
    {id && <p><Link to={`/organizer/events/${id}/participants`}>Участники и очередь ↗</Link></p>}
    {id && query.isPending ? <Loading /> : id && query.isError ? <><ErrorMessage error={query.error} /><button onClick={() => void query.refetch()}>Повторить</button></> :
      <EditorForm key={id || 'new'} token={token} event={id ? query.data : undefined} />}
  </main>
}

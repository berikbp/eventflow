import { useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { useMutation } from '@tanstack/react-query'
import { verifyOrganizer } from '../api/events'
import { ErrorMessage } from './Feedback'

export function OrganizerAccess({ token, onToken, children }: {
  token: string; onToken: (token: string) => void; children: ReactNode
}) {
  const [input, setInput] = useState('')
  const access = useMutation({
    mutationFn: verifyOrganizer,
    onSuccess: (_, checkedToken) => { onToken(checkedToken); setInput('') },
  })
  if (token) return children
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    access.mutate(input.trim())
  }
  return <main className="narrow">
    <span className="eyebrow">ДОСТУП ОРГАНИЗАТОРА</span>
    <h1>Управляйте мероприятиями</h1>
    <p className="intro">Введите токен доступа организатора. После обновления страницы потребуется войти снова.</p>
    <form onSubmit={submit} className="panel form">
      <label>Токен организатора<input type="password" required autoComplete="off" value={input} onChange={e => setInput(e.target.value)} /></label>
      <ErrorMessage error={access.error} />
      <button disabled={access.isPending || !input.trim()}>{access.isPending ? 'Проверяем…' : 'Продолжить'}</button>
    </form>
  </main>
}

export function toLocalInput(iso: string): string {
  const date = new Date(iso)
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 16)
}

export function toUtc(local: string): string {
  const date = new Date(local)
  if (!Number.isFinite(date.getTime())) throw new Error('Укажите корректную дату и время')
  return date.toISOString()
}

export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat('ru-RU', {
    dateStyle: 'long', timeStyle: 'short',
  }).format(new Date(iso))
}

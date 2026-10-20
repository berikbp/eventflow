import { request } from './client.ts'

export type Event = {
  id: string
  title: string
  description: string
  starts_at: string
  capacity: number
  schedule_version: number
  created_at: string
  updated_at: string
}
export type EventInput = Pick<Event, 'title' | 'description' | 'starts_at' | 'capacity'>
export type EventPage = { items: Event[]; total: number; limit: number; offset: number }

function headers(token: string) {
  return { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
}
export const listEvents = (offset = 0) => request<EventPage>(`/events?limit=20&offset=${offset}`)
export const getEvent = (id: string) => request<Event>(`/events/${encodeURIComponent(id)}`)
export const createEvent = (data: EventInput, token: string) => request<Event>('/events', {
  method: 'POST', headers: headers(token), body: JSON.stringify(data),
})
export const updateEvent = (id: string, data: Partial<EventInput>, token: string) => request<Event>(`/events/${encodeURIComponent(id)}`, {
  method: 'PATCH', headers: headers(token), body: JSON.stringify(data),
})
export const deleteEvent = (id: string, token: string) => request<void>(`/events/${encodeURIComponent(id)}`, {
  method: 'DELETE', headers: headers(token),
})
export async function verifyOrganizer(token: string): Promise<void> {
  const result = await request<{ authenticated: boolean }>('/organizer/session', { headers: headers(token) })
  if (result.authenticated !== true) throw new Error('Не удалось проверить доступ')
}

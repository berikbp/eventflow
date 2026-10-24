import { request } from './client.ts'

export type Registration = {
  id: string; event_id: string; email: string
  status: 'confirmed' | 'waiting' | 'cancelled'
  queue_order: number; queue_position: number | null
  created_at: string; updated_at: string; checked_in_at: string | null
}
export type Availability = {
  capacity: number; confirmed: number; waiting: number; available: number
  registration_open: boolean; checked_in: number
}
export type RegistrationPage = {
  items: Registration[]; total: number; limit: number; offset: number
}
export const registrationLabels = {
  confirmed: 'Участие подтверждено',
  waiting: 'В листе ожидания',
  cancelled: 'Регистрация отменена',
}
export const getAvailability = (eventId: string) =>
  request<Availability>(`/events/${encodeURIComponent(eventId)}/availability`)
export const registerForEvent = (eventId: string, email: string, token: string) =>
  request<Registration>(`/events/${encodeURIComponent(eventId)}/registrations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Registration-Token': token },
    body: JSON.stringify({ email }),
  })
export const getRegistration = (id: string, token: string) =>
  request<Registration>(`/registrations/${encodeURIComponent(id)}`, {
    headers: { Authorization: `Bearer ${token}` }, cache: 'no-store',
  })
export const changeParticipation = (id: string, token: string, action: 'cancel' | 'rejoin') =>
  request<Registration>(`/registrations/${encodeURIComponent(id)}/${action}`, {
    method: 'POST', headers: { Authorization: `Bearer ${token}` },
  })
export const listRegistrations = (eventId: string, token: string, offset = 0) =>
  request<RegistrationPage>(`/events/${encodeURIComponent(eventId)}/registrations?limit=20&offset=${offset}`, {
    headers: { Authorization: `Bearer ${token}` }, cache: 'no-store',
  })

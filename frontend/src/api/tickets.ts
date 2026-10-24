import { request } from './client.ts'

export type Ticket = {
  id: string; registration_id: string; code: string
  created_at: string; checked_in_at: string | null
}
export type TicketVerification = Ticket & {
  event_id: string; email: string
  status: 'valid' | 'checked_in' | 'revoked'; revoked_at: string | null
}
export type CheckInResult = { ticket: TicketVerification; already_checked_in: boolean }
export const getTicket = (id: string, token: string) =>
  request<Ticket | null>(`/registrations/${encodeURIComponent(id)}/ticket`, {
    headers: { Authorization: `Bearer ${token}` }, cache: 'no-store',
  })
export const verifyTicket = (eventId: string, code: string, token: string) =>
  request<TicketVerification>(`/events/${encodeURIComponent(eventId)}/tickets/verify`, {
    method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }), cache: 'no-store',
  })
export const checkIn = (eventId: string, code: string, token: string) =>
  request<CheckInResult>(`/events/${encodeURIComponent(eventId)}/check-in`, {
    method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }), cache: 'no-store',
  })

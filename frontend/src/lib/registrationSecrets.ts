export type RegistrationAttempt = { email: string; token: string }

export function newRegistrationToken(): string {
  return Array.from(crypto.getRandomValues(new Uint8Array(32)),
    byte => byte.toString(16).padStart(2, '0')).join('')
}
export function registrationPath(id: string, token: string): string {
  return `/registrations/${encodeURIComponent(id)}#token=${encodeURIComponent(token)}`
}
export function tokenFromHash(hash: string): string {
  const token = new URLSearchParams(hash.replace(/^#/, '')).get('token') || ''
  return /^[A-Za-z0-9_-]{43,128}$/.test(token) ? token : ''
}
export function pendingAttempt(eventId: string): RegistrationAttempt | null {
  try {
    const item = JSON.parse(sessionStorage.getItem(`registration-attempt:${eventId}`) || 'null')
    return item && typeof item.email === 'string' &&
      typeof item.token === 'string' && /^[A-Za-z0-9_-]{43,128}$/.test(item.token) ? item : null
  } catch { return null }
}
export function rememberAttempt(eventId: string, attempt: RegistrationAttempt | null) {
  try {
    if (attempt) sessionStorage.setItem(`registration-attempt:${eventId}`, JSON.stringify(attempt))
    else sessionStorage.removeItem(`registration-attempt:${eventId}`)
  } catch { /* In-memory retry remains available when storage is disabled. */ }
}

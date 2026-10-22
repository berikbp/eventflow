import assert from 'node:assert/strict'
import { test } from 'node:test'
import { changeParticipation, getRegistration, registerForEvent, listRegistrations } from '../src/api/registrations.ts'
import { newRegistrationToken, pendingAttempt, registrationPath, rememberAttempt, tokenFromHash } from '../src/lib/registrationSecrets.ts'

test('registration retries use a stable header credential, never a URL secret', async (t) => {
  const token = newRegistrationToken()
  let calls = 0
  t.mock.method(globalThis, 'fetch', async (url: string, options: RequestInit) => {
    calls++
    assert.equal(url, '/api/events/event-id/registrations')
    assert.equal(options.method, 'POST')
    assert.equal((options.headers as Record<string, string>)['X-Registration-Token'], token)
    assert.deepEqual(JSON.parse(options.body as string), { email: 'person@example.com' })
    return Response.json({ id: 'registration-id', status: 'waiting', queue_position: 1 })
  })
  assert.equal((await registerForEvent('event-id', 'person@example.com', token)).status, 'waiting')
  assert.equal((await registerForEvent('event-id', 'person@example.com', token)).id, 'registration-id')
  assert.equal(calls, 2)
})

test('status and cancellation send bearer credential only in the header', async (t) => {
  const token = newRegistrationToken()
  const paths: string[] = []
  t.mock.method(globalThis, 'fetch', async (url: string, options: RequestInit) => {
    assert.ok(!url.includes(token))
    assert.equal((options.headers as Record<string, string>).Authorization, `Bearer ${token}`)
    paths.push(url)
    return Response.json({ id: 'r', status: 'cancelled' })
  })
  await getRegistration('r', token)
  assert.equal((await changeParticipation('r', token, 'cancel')).status, 'cancelled')
  await changeParticipation('r', token, 'rejoin')
  assert.deepEqual(paths, ['/api/registrations/r', '/api/registrations/r/cancel', '/api/registrations/r/rejoin'])
})

test('management secret survives link roundtrip only in its fragment', () => {
  const token = newRegistrationToken()
  assert.match(token, /^[a-f0-9]{64}$/)
  const url = new URL(registrationPath('registration-id', token), 'http://localhost:5173')
  assert.equal(url.pathname, '/registrations/registration-id')
  assert.equal(url.search, '')
  assert.equal(tokenFromHash(url.hash), token)
  assert.equal(tokenFromHash('#token=short'), '')
})

test('pending attempt recovers after reload and is cleared after success', (t) => {
  const original = Object.getOwnPropertyDescriptor(globalThis, 'sessionStorage')
  const data = new Map<string, string>()
  Object.defineProperty(globalThis, 'sessionStorage', { configurable: true, value: {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => data.set(key, value),
    removeItem: (key: string) => data.delete(key),
  } })
  t.after(() => {
    if (original) Object.defineProperty(globalThis, 'sessionStorage', original)
    else Reflect.deleteProperty(globalThis, 'sessionStorage')
  })
  const attempt = { email: 'person@example.com', token: newRegistrationToken() }
  rememberAttempt('event', attempt)
  assert.deepEqual(pendingAttempt('event'), attempt)
  rememberAttempt('event', null)
  assert.equal(pendingAttempt('event'), null)
})

test('organizer participant list uses protected paginated endpoint', async (t) => {
  t.mock.method(globalThis, 'fetch', async (url: string, options: RequestInit) => {
    assert.equal(url, '/api/events/event/registrations?limit=20&offset=20')
    assert.equal((options.headers as Record<string, string>).Authorization, 'Bearer organizer')
    return Response.json({ items: [], total: 20, limit: 20, offset: 20 })
  })
  assert.equal((await listRegistrations('event', 'organizer', 20)).total, 20)
})

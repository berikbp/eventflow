import assert from 'node:assert/strict'
import { test } from 'node:test'
import { createEvent, deleteEvent, listEvents, verifyOrganizer } from '../src/api/events.ts'
import { toLocalInput, toUtc } from '../src/lib/dates.ts'

test('create sends bearer access and timezone-aware payload', async (t) => {
  const payload = { title: 'Meetup', description: '', starts_at: '2099-01-01T12:00:00Z', capacity: 5 }
  t.mock.method(globalThis, 'fetch', async (url: string, options: RequestInit) => {
    assert.equal(url, '/api/events')
    assert.equal(options.method, 'POST')
    assert.equal((options.headers as Record<string, string>).Authorization, 'Bearer test-token')
    assert.deepEqual(JSON.parse(options.body as string), payload)
    return Response.json({ id: 'event-id', ...payload })
  })
  assert.equal((await createEvent(payload, 'test-token')).id, 'event-id')
})

test('delete accepts empty 204 response', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => new Response(null, { status: 204 }))
  assert.equal(await deleteEvent('event-id', 'test-token'), undefined)
})

test('API validation and access errors are readable', async (t) => {
  const mock = t.mock.method(globalThis, 'fetch', async () => Response.json({ detail: 'Неверный токен организатора' }, { status: 401 }))
  await assert.rejects(verifyOrganizer('wrong'), /Неверный токен/)
  mock.mock.mockImplementation(async () => Response.json({ detail: [{ loc: ['body', 'capacity'], msg: 'Must be positive' }] }, { status: 422 }))
  await assert.rejects(listEvents(), /capacity: Must be positive/)
})

test('date conversion roundtrips local time without dropping timezone', () => {
  const iso = '2099-01-01T12:35:00.000Z'
  assert.equal(toUtc(toLocalInput(iso)), iso)
  assert.throws(() => toUtc('invalid'), /корректную дату/)
})

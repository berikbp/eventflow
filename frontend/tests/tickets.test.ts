import assert from 'node:assert/strict'
import { test } from 'node:test'
import { getTicket, verifyTicket, checkIn } from '../src/api/tickets.ts'

test('private ticket and organizer operations keep credentials and codes out of URLs', async (t) => {
  const paths: string[] = []
  t.mock.method(globalThis, 'fetch', async (url: string, options: RequestInit) => {
    paths.push(url)
    assert.equal(options.cache, 'no-store')
    assert.equal((options.headers as Record<string, string>).Authorization, 'Bearer secret')
    if (options.method === 'POST') assert.deepEqual(JSON.parse(options.body as string), { code: 'ABC' })
    return Response.json(url.endsWith('/ticket') ? null : { already_checked_in: true, status: 'revoked' })
  })
  assert.equal(await getTicket('r', 'secret'), null)
  assert.equal((await verifyTicket('e', 'ABC', 'secret')).status, 'revoked')
  assert.equal((await checkIn('e', 'ABC', 'secret')).already_checked_in, true)
  assert.deepEqual(paths, ['/api/registrations/r/ticket', '/api/events/e/tickets/verify', '/api/events/e/check-in'])
})

test('revoked ticket errors remain visible to the organizer', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => Response.json({ detail: 'Билет отозван' }, { status: 409 }))
  await assert.rejects(checkIn('e', 'ABC', 'secret'), /Билет отозван/)
})

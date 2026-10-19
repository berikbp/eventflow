import assert from 'node:assert/strict'
import { test } from 'node:test'
import { QueryClient } from '@tanstack/react-query'
import { checkHealth } from '../src/api/health.ts'

test('readiness succeeds through TanStack Query with defined data', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => Response.json({ status: 'ok', database: 'ok' }))
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  try {
    const result = await client.fetchQuery({ queryKey: ['readiness'], queryFn: checkHealth })
    assert.deepEqual(result, { status: 'ok', database: 'ok' })
    assert.equal(client.getQueryState(['readiness'])?.status, 'success')
  } finally {
    client.clear()
  }
})

test('readiness rejects an unavailable database', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => new Response(null, { status: 503 }))
  await assert.rejects(checkHealth(), /API или база данных недоступны/)
})

test('readiness rejects an unexpected response', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => Response.json({ status: 'ok' }))
  await assert.rejects(checkHealth(), /Неожиданный ответ API/)
})

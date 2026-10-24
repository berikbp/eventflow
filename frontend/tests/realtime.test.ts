import assert from 'node:assert/strict'
import { test } from 'node:test'
import { QueryClient } from '@tanstack/react-query'
import { connectUpdates } from '../src/lib/realtime.ts'

test('SSE invalidates active data, refreshes after reconnect, and closes on cleanup', async (t) => {
  t.mock.timers.enable({ apis: ['setTimeout'] })
  const instances: FakeSource[] = []
  class FakeSource {
    listeners = new Map<string, () => void>()
    onopen?: () => void
    onerror?: () => void
    closed = false
    constructor(url: string) { assert.equal(url, '/api/updates'); instances.push(this) }
    addEventListener(name: string, handler: () => void) { this.listeners.set(name, handler) }
    close() { this.closed = true }
  }
  const original = Object.getOwnPropertyDescriptor(globalThis, 'EventSource')
  Object.defineProperty(globalThis, 'EventSource', { configurable: true, value: FakeSource })
  t.after(() => {
    if (original) Object.defineProperty(globalThis, 'EventSource', original)
    else Reflect.deleteProperty(globalThis, 'EventSource')
  })
  const client = new QueryClient()
  for (const key of ['event', 'events', 'participants', 'registration', 'ticket', 'availability', 'readiness']) client.setQueryData([key], {})
  const statuses: boolean[] = []
  const close = connectUpdates(client, status => statuses.push(status))
  const source = instances[0]
  source.listeners.get('invalidate')!()
  for (const key of ['event', 'events', 'participants', 'registration', 'ticket', 'availability']) assert.equal(client.getQueryState([key])?.isInvalidated, true)
  assert.equal(client.getQueryState(['readiness'])?.isInvalidated, false)
  client.setQueryData(['event'], {})
  source.onerror!()
  source.onopen!()
  assert.equal(client.getQueryState(['event'])?.isInvalidated, true)
  assert.deepEqual(statuses, [true, false, true])
  t.mock.timers.tick(24000)
  source.listeners.get('heartbeat')!()
  t.mock.timers.tick(24000)
  assert.equal(instances.length, 1)
  t.mock.timers.tick(1001)
  assert.equal(source.closed, true)
  assert.equal(instances.length, 2)
  close()
  assert.equal(instances[1].closed, true)
  client.clear()
})

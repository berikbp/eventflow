import type { QueryClient } from '@tanstack/react-query'

const liveKeys = new Set(['events', 'event', 'availability', 'participants', 'registration', 'ticket'])

export function connectUpdates(client: QueryClient, onStatus: (connected: boolean) => void) {
  let source: EventSource
  let watchdog: ReturnType<typeof setTimeout>
  let stopped = false
  const alive = () => {
    clearTimeout(watchdog)
    onStatus(true)
    // Detect half-open proxy/network connections as well as explicit errors.
    watchdog = setTimeout(() => {
      source.close()
      onStatus(false)
      open()
    }, 25000)
  }
  const refresh = () => {
    alive()
    void client.invalidateQueries({ predicate: query => liveKeys.has(String(query.queryKey[0])) })
  }
  const open = () => {
    if (stopped) return
    source = new EventSource('/api/updates')
    source.addEventListener('invalidate', refresh)
    source.addEventListener('heartbeat', alive)
    source.onopen = refresh
    source.onerror = () => onStatus(false)
    source.addEventListener('unavailable', () => onStatus(false))
  }
  open()
  return () => { stopped = true; clearTimeout(watchdog); source.close() }
}

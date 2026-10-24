import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { connectUpdates } from '../lib/realtime'

export function RealtimeStatus() {
  const client = useQueryClient()
  const [connected, setConnected] = useState(false)
  useEffect(() => connectUpdates(client, setConnected), [client])
  return <p className="live-status" role="status">{connected
    ? 'Обновления подключены'
    : 'Подключаем обновления… При обрыве данные проверяются каждые 10 секунд.'}</p>
}

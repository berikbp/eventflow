type Readiness = { status: 'ok'; database: 'ok' }

export async function checkHealth(): Promise<Readiness> {
  const response = await fetch('/api/health/ready', { signal: AbortSignal.timeout(8000) })
  if (!response.ok) throw new Error('API или база данных недоступны')
  const result: unknown = await response.json()
  if (
    typeof result !== 'object' || result === null ||
    !('status' in result) || result.status !== 'ok' ||
    !('database' in result) || result.database !== 'ok'
  ) throw new Error('Неожиданный ответ API')
  return { status: result.status, database: result.database }
}

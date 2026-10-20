export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api${path}`, { ...options, signal: AbortSignal.timeout(10000) })
  } catch {
    throw new Error('Не удалось связаться с сервером. Проверьте подключение и повторите попытку.')
  }
  if (!response.ok) {
    let message = `Ошибка запроса (${response.status})`
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') message = body.detail
      else if (Array.isArray(body.detail)) {
        message = body.detail.map((item: { loc?: string[]; msg?: string }) =>
          `${item.loc?.slice(1).join('.') || 'Данные'}: ${item.msg || 'некорректное значение'}`,
        ).join('; ')
      }
    } catch { /* Proxy failures can return non-JSON responses. */ }
    throw new ApiError(message, response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

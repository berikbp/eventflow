import { useQuery } from '@tanstack/react-query'
import { Link, Route, Routes } from 'react-router-dom'
import { checkHealth } from './api/health'

function Foundation() {
  const health = useQuery({ queryKey: ['readiness'], queryFn: checkHealth, retry: 1, refetchInterval: 15000 })
  return (
    <main>
      <span className="eyebrow">PHASE 01 · PROJECT FOUNDATION</span>
      <h1>Мероприятия начинаются<br />с надёжной основы.</h1>
      <p className="intro">EventFlow — система регистрации на мероприятия. Сейчас подготовлена инфраструктура; мероприятия, билеты и лист ожидания появятся на следующих этапах.</p>
      <section aria-labelledby="status-title" className="status-card">
        <div><span className="eyebrow">СОСТОЯНИЕ СИСТЕМЫ</span><h2 id="status-title">Подключение к API и PostgreSQL</h2></div>
        <p role="status" className={health.isError ? 'error' : 'status'}>
          {health.isPending ? 'Проверяем подключение…' : health.isError ? health.error.message : 'API отвечает · PostgreSQL подключён'}
        </p>
        <button disabled={health.isFetching} onClick={() => void health.refetch()}>{health.isFetching ? 'Проверяем…' : 'Проверить снова'}</button>
      </section>
      <p className="footnote">Проверка обновляется каждые 15 секунд. Это техническая проверка доступности, а не real-time статистика мероприятий.</p>
    </main>
  )
}

export default function App() {
  return <><header><Link to="/" className="brand">eventflow<span>↗</span></Link><span>Регистрация. Участие. Впечатления.</span></header><Routes><Route path="/" element={<Foundation />} /><Route path="*" element={<main><h1>Страница не найдена</h1><Link to="/">На главную</Link></main>} /></Routes></>
}

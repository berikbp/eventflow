// UI error/loading/empty states and 320px layout. Requires the same Chrome/Compose
// setup as smoke_phase5_browser.mjs. Only list responses are intercepted below;
// ticket cancellation/check-in use the real API. Cleanup command: docs/testing.md.
import fs from 'node:fs/promises'
import assert from 'node:assert/strict'
import { randomBytes } from 'node:crypto'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { connectTab } from './browser.mjs'

const root = fileURLToPath(new URL('../../', import.meta.url))
const origin = process.env.EVENTFLOW_URL || 'http://127.0.0.1:5173'
const env = await fs.readFile(join(root, '.env'), 'utf8')
const organizerToken = env.match(/^ORGANIZER_TOKEN=(.*)$/m)[1].trim().replace(/^['"]|['"]$/g, '')
const auth = { Authorization: `Bearer ${organizerToken}`, 'Content-Type': 'application/json' }
const tabs = []
async function tab(path) {
  const page = await connectTab('/system')
  await page.send('Emulation.setDeviceMetricsOverride', {width:320,height:850,deviceScaleFactor:1,mobile:true})
  await page.navigate(path)
  tabs.push(page)
  return page
}
async function authorize(page) {
  await page.fill('input[type=password]', organizerToken)
  await page.click('Продолжить')
}
async function narrow(page) {
  await page.send('Page.bringToFront')
  await page.evaluate('document.activeElement?.blur(); document.documentElement.style.scrollBehavior="auto"; scrollTo(0,0)')
  await page.wait('document.documentElement.scrollWidth <= document.documentElement.clientWidth')
}
const title = 'Phase 6 ' + 'x'.repeat(190)
let event
try {
  const list = await tab('/system')
  await list.send('Page.bringToFront')
  // Hold list responses to check loading; then supply empty and unavailable cases.
  let status = 200
  let payload = { items: [], total: 0, limit: 20, offset: 0 }
  let holding = true
  const paused = []
  const fulfill = requestId => list.send('Fetch.fulfillRequest', {
    requestId, responseCode: status,
    responseHeaders: [{ name: 'Content-Type', value: 'application/json' }],
    body: Buffer.from(JSON.stringify(payload)).toString('base64'),
  })
  list.ws.addEventListener('message', message => {
    const frame = JSON.parse(message.data)
    if (frame.method === 'Fetch.requestPaused') {
      if (holding) paused.push(frame.params.requestId)
      else void fulfill(frame.params.requestId)
    }
  })
  await list.send('Fetch.enable', { patterns: [{ urlPattern: origin + '/api/events*' }] })
  await list.send('Emulation.setDeviceMetricsOverride', {width:320,height:850,deviceScaleFactor:1,mobile:true})
  await list.navigate('/')
  await list.wait("document.body?.textContent.includes('Загружаем данные…')")
  holding = false
  await Promise.all(paused.map(fulfill))
  await list.text('Мероприятий пока нет')
  await narrow(list)
  status = 503
  payload = { detail: 'База данных временно недоступна. Повторите запрос.' }
  await list.send('Page.reload')
  await list.text(payload.detail)
  assert.equal(await list.evaluate("document.body.innerText.includes('Мероприятий пока нет')"), false)
  status = 200
  payload = { items: [], total: 0, limit: 20, offset: 0 }
  await list.click('Повторить')
  await list.text('Мероприятий пока нет')
  await list.send('Fetch.disable')
  await list.close()

  const invalid = await tab('/events/not-a-uuid')
  await invalid.wait("!!document.querySelector('[role=alert]')")
  assert.equal(await invalid.evaluate("!!document.querySelector('input[type=email]')"), false)
  await invalid.navigate('/registrations/00000000-0000-4000-8000-000000000000')
  await invalid.text('Откройте полную личную ссылку')
  await invalid.navigate('/unknown-phase6-route')
  await invalid.text('Страница не найдена')
  await invalid.close()

  const created = await fetch(origin + '/api/events', {
    method: 'POST', headers: auth,
    body: JSON.stringify({ title, description: 'word'.repeat(700), capacity: 1,
      starts_at: new Date(Date.now() + 72 * 3600000).toISOString() }),
  })
  assert.equal(created.status, 201)
  event = await created.json()
  const state = join(tmpdir(), 'eventflow-phase6-browser-state.json')
  const previous = JSON.parse(await fs.readFile(state, 'utf8').catch(() => '[]'))
  await fs.writeFile(state, JSON.stringify([...previous, { eid: event.id }]), { mode: 0o600 })
  const key = randomBytes(32).toString('hex')
  const registration = await fetch(origin + `/api/events/${event.id}/registrations`, {
    method: 'POST', headers: { 'X-Registration-Token': key, 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'phase6-browser@example.com' }),
  })
  assert.equal(registration.status, 200)
  const record = await registration.json()
  const ticketResponse = await fetch(origin + `/api/registrations/${record.id}/ticket`, {
    headers: { Authorization: `Bearer ${key}` },
  })
  const ticket = await ticketResponse.json()
  const check = await tab(`/organizer/events/${event.id}/check-in`)
  await check.fill('input[type=password]', 'wrong-token')
  await check.click('Продолжить')
  await check.text('Неверный токен организатора')
  await authorize(check)
  await check.fill('.checkin-layout input[placeholder]', ticket.code)
  await check.click('Проверить билет')
  await check.text('Билет действителен')
  const cancel = await fetch(origin + `/api/registrations/${record.id}/cancel`, {
    method: 'POST', headers: { Authorization: `Bearer ${key}` },
  })
  assert.equal(cancel.status, 200)
  await check.click('Подтвердить вход')
  await check.text('Билет отозван или регистрация не подтверждена')
  assert.equal(await check.evaluate("document.body.innerText.includes('Билет действителен')"), false)
  await narrow(check)
  await check.click('Участники и статистика')
  await check.text('Регистрации: 1')
  await narrow(check)
  await check.click('Редактировать мероприятие')
  await check.wait("!!document.querySelector('input[type=number]')")
  await check.fill('input[type=number]', '0')
  assert.equal(await check.evaluate("document.querySelector('input[type=number]').checkValidity()"), false)
  await narrow(check)
  const publicPage = await tab(`/events/${event.id}`)
  await publicPage.text(title)
  await narrow(publicPage)
  const personal = await tab(`/registrations/${record.id}#token=${key}`)
  await personal.text('Регистрация отменена')
  await narrow(personal)
  const snapshot = await personal.send('Page.captureScreenshot', { format: 'png' })
  await fs.writeFile(join(tmpdir(), 'eventflow-phase6-mobile.png'), Buffer.from(snapshot.data, 'base64'))
  for (const page of tabs) assert.deepEqual(page.errors, [])
  console.log('Phase 6 browser passed: loading, empty, error/retry, 404, invalid access, native validation, revoked check-in, five layouts at 320px')
} finally {
  await Promise.all(tabs.map(page => page.close()))
}

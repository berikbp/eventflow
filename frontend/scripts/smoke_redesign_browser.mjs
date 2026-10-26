// Real API/browser verification for EventFlow's redesigned discovery and ticket flow.
// Requires running Compose and a separate Chrome CDP profile; see docs/testing.md.
import fs from 'node:fs/promises'
import assert from 'node:assert/strict'
import { join } from 'node:path'
import { tmpdir } from 'node:os'
import { fileURLToPath } from 'node:url'
import { connectTab } from './browser.mjs'

const root = fileURLToPath(new URL('../../', import.meta.url))
const output = join(root, '.impeccable/review')
await fs.mkdir(output, { recursive: true })
const origin = process.env.EVENTFLOW_URL || 'http://127.0.0.1:5173'
const env = await fs.readFile(join(root, '.env'), 'utf8')
const organizerToken = env.match(/^ORGANIZER_TOKEN=(.*)$/m)[1].trim().replace(/^['"]|['"]$/g, '')
const tabs = []
const tab = async path => { const value = await connectTab(path); tabs.push(value); return value }
async function api(path, { data, method, token, key } = {}) {
  const response = await fetch(origin + '/api' + path, {
    method: method || (data ? 'POST' : 'GET'),
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(key ? { 'X-Registration-Token': key } : {}) },
    ...(data ? { body: JSON.stringify(data) } : {}),
  })
  assert.ok(response.ok, `API response ${response.status}`)
  return response.json()
}
async function capture(page, filename, width = 1440, height = 1000) {
  await page.send('Page.bringToFront')
  await page.send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: width < 600 })
  await page.evaluate('document.documentElement.style.scrollBehavior="auto"; scrollTo(0,0)')
  await page.evaluate('document.fonts.ready')
  await page.wait('[...document.images].every(image => image.complete)')
  await page.evaluate('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
  await page.wait('document.documentElement.scrollWidth <= document.documentElement.clientWidth')
  const size = (await page.send('Page.getLayoutMetrics')).cssContentSize
  const screenshot = await page.send('Page.captureScreenshot', {
    format: 'png', captureBeyondViewport: true,
    clip: { x: 0, y: 0, width: size.width, height: size.height, scale: 1 },
  })
  await fs.writeFile(join(output, filename), Buffer.from(screenshot.data, 'base64'))
}
try {
  const home = await tab('/')
  await home.text('Хорошие события.')
  await home.wait('document.querySelectorAll(".event-card").length > 0')
  await capture(home, 'desktop.png')
  await capture(home, 'user-1280.png', 1280, 900)
  await capture(home, 'mobile.png', 390, 844)
  await capture(home, 'user-320.png', 320, 850)
  await home.fill('input[aria-label="Поиск мероприятия"]', 'PostgreSQL')
  await home.evaluate('document.querySelector("form[role=search]").requestSubmit()')
  await home.wait('document.querySelectorAll(".event-card").length === 1')
  assert.match(await home.evaluate('document.querySelector(".event-card h3").textContent'), /PostgreSQL/)
  await home.fill('input[aria-label="Поиск мероприятия"]', '__no_such_event__')
  await home.evaluate('document.querySelector("form[role=search]").requestSubmit()')
  await home.text('Событий по вашему запросу нет')
  await home.click('Сбросить фильтры')
  await home.wait('document.querySelectorAll(".event-card").length > 0')
  await home.evaluate(`(() => {const select=document.querySelector('select[aria-label="Период мероприятий"]');select.value='week';select.dispatchEvent(new Event('change',{bubbles:true}))})()`)
  await home.wait('location.search.includes("period=week")')
  const start = new Date()
  const finish = new Date(start.getTime() + 7 * 86400000)
  const expected = await api('/events?' + new URLSearchParams({ limit: '20', starts_after: start.toISOString(), starts_before: finish.toISOString() }))
  await home.wait(`document.querySelectorAll('.event-card').length === ${expected.items.length}`)
  const dates = await home.evaluate("[...document.querySelectorAll('.event-card time')].map(node=>node.dateTime)")
  assert.ok(dates.every(date=>new Date(date)>=start && new Date(date)<finish))
  await home.navigate('/#how-it-works')
  await home.text('Аккаунт создавать не нужно.')
  await home.click('Можно прийти без регистрации?')
  await home.text('Для входа нужен действующий билет.')
  const seeded = await tab('/events/00000000-0000-4000-8000-000000000001')
  await seeded.text('Об этом событии')
  await capture(seeded, 'event-desktop.png')
  await capture(seeded, 'event-mobile.png', 390, 844)
  const created = await api('/events', { token: organizerToken, data: { title: 'EventFlow UI review — тест', description: 'Временное синтетическое событие для проверки регистрации и интерфейса.', capacity: 1, starts_at: new Date(Date.now()+72*3600000).toISOString() } })
  const statePath = join(tmpdir(), 'eventflow-redesign-browser-state.json')
  const previous = JSON.parse(await fs.readFile(statePath, 'utf8').catch(() => '[]'))
  await fs.writeFile(statePath, JSON.stringify([...previous, {eid: created.id}]), {mode:0o600})
  const participant = await tab(`/events/${created.id}`)
  await participant.fill('input[type=email]', 'ui-review@example.com')
  await participant.click('Зарегистрироваться')
  await participant.text('Участие подтверждено')
  await participant.wait('!!document.querySelector(".ticket-code")')
  await participant.text('Сохраните вашу личную ссылку')
  await capture(participant, 'ticket-desktop.png')
  await capture(participant, 'ticket-mobile.png', 390, 844)
  const organizer = await tab(`/organizer/events/${created.id}/participants`)
  await organizer.fill('input[type=password]', organizerToken)
  await organizer.click('Продолжить')
  await organizer.text('ui-review@example.com')
  await capture(organizer, 'organizer-desktop.png')
  await capture(organizer, 'organizer-mobile.png', 390, 844)
  const unknown = await tab('/unknown-redesign-route')
  await unknown.text('Страница не найдена')
  await capture(unknown, 'error-mobile.png', 390, 844)
  for(const page of tabs) assert.deepEqual(page.errors, [])
  console.log('Redesign browser passed: discovery search, empty/reset, period filter, registration explanation, real email signup/ticket, organizer and 1440/1280/390/320px captures')
} finally {
  await Promise.all(tabs.map(page => page.close()))
}

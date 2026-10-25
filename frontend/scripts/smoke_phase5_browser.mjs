// Optional live E2E. Requires Chrome with remote debugging and running Compose.
// Stops/restarts the backend to test reconnection. Leaves scoped state for cleanup.
// No extra npm dependencies; see docs/testing.md. Never prints access credentials.
import fs from 'node:fs/promises'
import { connectTab } from './browser.mjs'
import {execFile} from 'node:child_process'
import {promisify} from 'node:util'
import assert from 'node:assert/strict'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
const root = fileURLToPath(new URL('../../', import.meta.url))
const statePath = join(tmpdir(), 'eventflow-phase5-browser-state.json')
const debugOrigin = process.env.CHROME_DEBUG_URL || 'http://127.0.0.1:9222'

const origin = process.env.EVENTFLOW_URL || 'http://127.0.0.1:5173'
const env = await fs.readFile(join(root, '.env'), 'utf8')
const token = env.match(/^ORGANIZER_TOKEN=(.*)$/m)[1].trim().replace(/^['"]|['"]$/g, '')
async function api(path, body, organizer = false) {
  const response = await fetch(origin + '/api' + path, { method: body ? 'POST' : 'GET', headers: { ...(organizer ? {Authorization: `Bearer ${token}`} : {}), 'Content-Type': 'application/json' }, ...(body ? {body: JSON.stringify(body)} : {}) })
  assert.ok(response.ok, `API failed ${response.status}`)
  return response.json()
}
for (const page of await (await fetch(debugOrigin+'/json/list')).json()) {
  if (page.type === 'page' && page.url.startsWith(origin)) await fetch(debugOrigin+'/json/close/'+page.id)
}
const event = await api('/events', {title: 'Phase 5 browser smoke', capacity: 1, starts_at: new Date(Date.now() + 72*3600000).toISOString()}, true)
const previous=JSON.parse(await fs.readFile(statePath,'utf8').catch(()=> '[]'));
await fs.writeFile(statePath, JSON.stringify([...(Array.isArray(previous)?previous:[previous]),{eid:event.id}]), {mode:0o600})
const tab = path => connectTab(path, { origin, debugOrigin })
const organizer=await tab(`/organizer/events/${event.id}/participants`)
const participant=await tab(`/events/${event.id}`)
try {
  await organizer.fill('input[type=password]',token); await organizer.click('Продолжить')
  await organizer.text('Пока никто не зарегистрировался.')
  await participant.fill('input[type=email]','phase5-browser-a@example.com')
  const started=Date.now(); await participant.click('Зарегистрироваться'); await participant.text('Ваш билет')
  await organizer.text('phase5-browser-a@example.com',5000)
  const latency=Date.now()-started; assert.ok(latency<6000)
  const firstLink=await participant.evaluate('location.pathname+location.hash')
  await participant.navigate(`/events/${event.id}`)
  await participant.fill('input[type=email]','phase5-browser-b@example.com'); await participant.click('Встать в очередь')
  await participant.text('В листе ожидания'); await organizer.text('phase5-browser-b@example.com',5000)
  const waitingLink=await participant.evaluate('location.pathname+location.hash')
  // Cancel using A's saved private credential while B and organizer remain open.
  const a = new URL(firstLink, origin)
  const key=new URLSearchParams(a.hash.slice(1)).get('token')
  const cancelled=await fetch(origin+'/api'+a.pathname+'/cancel',{method:'POST',headers:{Authorization:`Bearer ${key}`}})
  assert.equal(cancelled.status,200)
  await participant.text('Ваш билет',5000)
  await participant.wait("!!document.querySelector('.ticket-code')")
  const code=(await participant.evaluate("document.querySelector('.ticket-code').textContent")).replaceAll(' ','')
  await organizer.click('Проверка билетов и check-in')
  await organizer.fill('input[placeholder]',code); await organizer.click('Проверить билет'); await organizer.text('Билет действителен')
  await organizer.click('Подтвердить вход'); await organizer.text('Check-in выполнен.')
  await participant.text('Вход отмечен:',5000)
  await organizer.click('Проверить билет'); await organizer.text('Вход уже зарегистрирован')
  await organizer.click('← Участники и статистика')
  await organizer.wait("[...document.querySelectorAll('dt')].find(x=>x.textContent==='Прошли check-in')?.nextElementSibling.textContent==='1'")
  // Rescheduling updates the other tab's event details without navigation/reload.
  await participant.navigate(`/events/${event.id}`); await participant.text('Phase 5 browser smoke')
  const changed=await fetch(origin+`/api/events/${event.id}`,{method:'PATCH',headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},body:JSON.stringify({title:'Phase 5 updated live',starts_at:new Date(Date.now()+12*3600000).toISOString()})}); assert.equal(changed.status,200)
  await participant.text('Phase 5 updated live',5000); await organizer.text('Phase 5 updated live',5000)
  // Stop/restart the actual server: all EventSource connections must reconnect.
  await promisify(execFile)('docker',['compose','stop','backend'],{cwd:root})
  await participant.text('Подключаем обновления',6000)
  await promisify(execFile)('docker',['compose','up','-d','--wait','backend'],{cwd:root})
  const recovery=await fetch(origin+`/api/events/${event.id}`,{method:'PATCH',headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},body:JSON.stringify({title:'Phase 5 reconnected'})}); assert.equal(recovery.status,200)
  await participant.text('Phase 5 reconnected',6000)
  await participant.text('Обновления подключены',6000)
  await organizer.text('Phase 5 reconnected',6000)
  await organizer.send('Page.bringToFront')
  await organizer.send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false})
  const desktop=await organizer.send('Page.captureScreenshot',{format:'png'}); await fs.writeFile(join(tmpdir(),'eventflow-phase5-dashboard.png'),Buffer.from(desktop.data,'base64'))
  await participant.navigate(waitingLink); await participant.text('Ваш билет')
  await participant.send('Page.bringToFront')
  await participant.send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true})
  await participant.wait('document.documentElement.scrollWidth<=window.innerWidth')
  const mobile=await participant.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true}); await fs.writeFile(join(tmpdir(),'eventflow-phase5-mobile.png'),Buffer.from(mobile.data,'base64'))
  assert.deepEqual(organizer.errors,[]); assert.deepEqual(participant.errors,[])
  console.log(`Two-tab browser smoke passed: registration visible in ${latency}ms, waiting, promotion, check-in, attendance, reschedule, reconnect, mobile width`)
} finally {
  await promisify(execFile)('docker',['compose','up','-d','--wait','backend'],{cwd:root})
  await Promise.all([organizer.close(), participant.close()])
}

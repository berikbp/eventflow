// Minimal CDP helpers for the optional live smoke scripts; no npm dependencies.
export class Tab {
  constructor(ws) {
    this.ws = ws
    this.sequence = 0
    this.pending = new Map()
    this.errors = []
    ws.addEventListener('message', event => {
      const message = JSON.parse(event.data)
      if (message.id) {
        const pending = this.pending.get(message.id)
        this.pending.delete(message.id)
        if (pending) {
          if (message.error) pending.reject(new Error(message.error.message))
          else pending.resolve(message.result)
        }
      }
      if (message.method === 'Runtime.exceptionThrown') {
        this.errors.push(message.params.exceptionDetails.text)
      }
    })
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++this.sequence
      const timer = setTimeout(() => {
        this.pending.delete(id)
        reject(new Error('CDP timed out: ' + method))
      }, 20000)
      this.pending.set(id, {
        resolve: result => { clearTimeout(timer); resolve(result) },
        reject: error => { clearTimeout(timer); reject(error) },
      })
      this.ws.send(JSON.stringify({ id, method, params }))
    })
  }

  async evaluate(expression) {
    const result = await this.send('Runtime.evaluate', {
      expression, returnByValue: true, awaitPromise: true,
    })
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.text)
    return result.result.value
  }

  async wait(expression, timeout = 12000) {
    const end = Date.now() + timeout
    while (Date.now() < end) {
      if (await this.evaluate(expression)) return
      await new Promise(resolve => setTimeout(resolve, 50))
    }
    throw new Error('Browser assertion timed out: ' + expression)
  }

  text(text, timeout) {
    return this.wait(`document.body?.innerText.includes(${JSON.stringify(text)})`, timeout)
  }

  click(text) {
    return this.evaluate(`(() => {
      const button = [...document.querySelectorAll('button,a,summary')]
        .find(node => node.textContent.trim() === ${JSON.stringify(text)})
      if (!button) throw new Error('Button missing')
      button.click()
    })()`)
  }

  async fill(selector, value) {
    await this.wait(`!!document.querySelector(${JSON.stringify(selector)})`)
    await this.evaluate(`(() => {
      const input = document.querySelector(${JSON.stringify(selector)})
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')
        .set.call(input, ${JSON.stringify(value)})
      input.dispatchEvent(new Event('input', { bubbles: true }))
    })()`)
  }

  async close() {
    if (!this.closed) {
      this.closed = true
      await fetch(this.debugOrigin + '/json/close/' + this.targetId)
      this.ws.close()
    }
  }

  async navigate(url) {
    await this.send('Page.navigate', { url: new URL(url, this.origin).href })
  }
}

export async function connectTab(path, {
  origin = process.env.EVENTFLOW_URL || 'http://127.0.0.1:5173',
  debugOrigin = process.env.CHROME_DEBUG_URL || 'http://127.0.0.1:9222',
} = {}) {
  const response = await fetch(debugOrigin + '/json/new?' + encodeURIComponent(origin + path), {
    method: 'PUT',
  })
  const target = await response.json()
  const ws = new WebSocket(target.webSocketDebuggerUrl)
  await new Promise((resolve, reject) => {
    ws.addEventListener('open', resolve, { once: true })
    ws.addEventListener('error', reject, { once: true })
  })
  const tab = new Tab(ws)
  tab.origin = origin
  tab.debugOrigin = debugOrigin
  tab.targetId = target.id
  await tab.send('Runtime.enable')
  await tab.send('Page.enable')
  return tab
}

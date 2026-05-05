import { ElNotification } from 'element-plus'

/** Dedupe identical errors so SSE/render loops do not spam toasts */
let lastSig = ''
let lastAt = 0
const DEDUP_MS = 4000

function notificationMessage(err: unknown): string {
  if (err instanceof Error) {
    return err.message || String(err)
  }
  return String(err)
}

/** Global Vue error handler */
const errorHandler = (err: any) => {
  if (err?.status || err?.status === 0) {
    return false
  }
  const errorMap: { [key: string]: string } = {
    InternalError: 'Internal JavaScript engine error',
    ReferenceError: 'Reference not found',
    TypeError: 'Invalid type or object usage',
    RangeError: 'Argument out of range',
    SyntaxError: 'Syntax error',
    EvalError: 'Invalid use of eval',
    URIError: 'URI error',
  }
  console.error(err)

  const msg = notificationMessage(err)
  const title = errorMap[err?.name] || 'Unknown error'
  const now = Date.now()
  const sig = `${title}:${msg}`
  if (sig === lastSig && now - lastAt < DEDUP_MS) {
    return false
  }
  lastSig = sig
  lastAt = now

  ElNotification({
    title,
    message: msg,
    type: 'error',
    duration: 4500,
  })
}

export default errorHandler

import { ElNotification } from 'element-plus'

/** Global Vue error handler */
const errorHandler = (error: any) => {
  if (error.status || error.status === 0) {
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
  console.error(error)
  const errorName = errorMap[error.name] || 'Unknown error'
  ElNotification({
    title: errorName,
    message: error,
    type: 'error',
    duration: 3000,
  })
}

export default errorHandler

/**
 * HTTP status messages for legacy axios wrappers (removed). Kept for reuse.
 */
export const statusMessages: Record<number, string> = {
  400: 'Bad request. Please try again later.',
  401: 'Session expired. Please sign in again.',
  403: 'You do not have permission to access this resource.',
  404: 'The resource was not found.',
  405: 'Method not allowed.',
  408: 'Request timed out.',
  500: 'Server error.',
  502: 'Bad gateway.',
  503: 'Service unavailable.',
  504: 'Gateway timeout.',
}

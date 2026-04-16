import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

NProgress.configure({
  easing: 'ease', // CSS easing
  speed: 500, // Increment speed (ms)
  showSpinner: true, // Show top-right spinner
  trickleSpeed: 200, // Trickle interval (ms)
  minimum: 0.3, // Minimum progress (0–1)
})

export default NProgress

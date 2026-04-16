/**
 * v-copy — copy a value to the clipboard.
 * Value: string | Ref<string> | Reactive<string>
 */

import type { Directive, DirectiveBinding } from 'vue'
import { ElMessage } from 'element-plus'
interface ElType extends HTMLElement {
  copyData: string | number
}
const copy: Directive = {
  mounted(el: ElType, binding: DirectiveBinding) {
    el.copyData = binding.value
    el.addEventListener('click', () => void handleClick(el))
  },
  updated(el: ElType, binding: DirectiveBinding) {
    el.copyData = binding.value
  },
  beforeUnmount(el: ElType) {
    el.removeEventListener('click', () => void handleClick(el))
  },
}

async function handleClick({ copyData }: any) {
  try {
    await navigator.clipboard.writeText(copyData)
    ElMessage({
      type: 'success',
      message: 'Copied to clipboard',
    })
  } catch (err) {
    console.error('Copy failed or is not supported: ', err)
  }
}

export default copy

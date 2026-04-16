/*
  Page background watermark.

  1. Render text on a canvas to a base64 PNG; set font size and color.
  2. Apply as CSS background on the host element.

  Usage: pass label, color, and optional font.
  <div v-waterMarker="{text:'All rights reserved',textColor:'rgba(180, 180, 180, 0.4)'}"></div>
*/

import type { Directive, DirectiveBinding } from 'vue'
const addWaterMarker = (str: string, parentNode: HTMLElement, font: any, textColor: string) => {
  // str, parent, font, textColor
  const can: HTMLCanvasElement = document.createElement('canvas')
  parentNode.appendChild(can)
  can.width = 205
  can.height = 140
  can.style.display = 'none'
  const cans = can.getContext('2d') as CanvasRenderingContext2D
  cans.rotate((-20 * Math.PI) / 180)
  cans.font = font || '16px Microsoft JhengHei'
  cans.fillStyle = textColor || 'rgba(180, 180, 180, 0.3)'
  cans.textAlign = 'left'
  cans.textBaseline = 'Middle' as CanvasTextBaseline
  cans.fillText(str, can.width / 10, can.height / 2)
  parentNode.style.backgroundImage = 'url(' + can.toDataURL('image/png') + ')'
}

const waterMarker = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    addWaterMarker(binding.value.text, el, binding.value.font, binding.value.textColor)
  },
}

export default waterMarker

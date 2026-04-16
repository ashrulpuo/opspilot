// @see https://unocss.dev/guide/config-file

import {
  defineConfig,
  presetWind4,
  presetAttributify,
  presetIcons,
  presetWebFonts,
  presetTypography,
  transformerDirectives,
  transformerVariantGroup,
} from 'unocss'
import { FileSystemIconLoader } from 'unplugin-icons/loaders'
import { readdirSync } from 'node:fs'
import { resolve } from 'node:path'

const iconsDir = './src/assets/icons/svg'

// Safelist all local SVG icons (e.g. icon picker). Remove if you only need on-demand icons.
const generateLocalIconSafelist = () => {
  const iconPath = resolve(iconsDir)
  const files = readdirSync(iconPath)
  return files.filter(file => file.endsWith('.svg')).map(file => `i-localSvgIcon:${file.replace('.svg', '')}`)
}

export default defineConfig({
  theme: {
    colors: {
      primary: 'var(--el-color-primary)',
      primary_dark: 'var(--el-color-primary-light-5)',
    },
  },
  presets: [
    presetWind4({
      preflights: {
        reset: true,
      },
    }),
    presetAttributify(),

    presetIcons({
      autoInstall: true,
      // Icon collection options
      collections: {
        localSvgIcon: FileSystemIconLoader(iconsDir, svg => {
          return svg.includes('fill="') ? svg : svg.replace(/^<svg /, '<svg fill="currentColor" ')
        }),
      },
      prefix: 'i-',
      extraProperties: {
        display: 'inline-block',
        width: '1em',
        height: '1em',
        'vertical-align': 'middle',
      },
      scale: 1.2,
    }),
    presetTypography(),
    presetWebFonts({
      fonts: {
        // ...
      },
    }),
  ],
  safelist: generateLocalIconSafelist(),
  transformers: [transformerDirectives(), transformerVariantGroup()],
})

import { createI18n } from 'vue-i18n'

import en from './en.json'

const i18n = createI18n({
  allowComposition: true,
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages: { en },
})

const { t } = i18n.global

export const localeMapping = {
  en: 'English',
} as const

const messageLocales = i18n.global.availableLocales
for (const locale of messageLocales) {
  if (!localeMapping[locale as keyof typeof localeMapping]) {
    // eslint-disable-next-line no-console
    console.warn(t(`error.localeNotSupported`, { locale }))
  }
}

export default i18n

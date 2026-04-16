import type { PersistenceOptions } from 'pinia-plugin-persistedstate'

/**
 * @description Pinia persisted-state options helper
 * @param {String} key localStorage key
 * @param {Array} pick state keys to persist (optional)
 * @return persist
 * */
const piniaPersistConfig = (key: string, pick?: string[]) => {
  const persist: PersistenceOptions = {
    key,
    storage: localStorage,
    // storage: sessionStorage,
    pick,
  }
  return persist
}

export default piniaPersistConfig

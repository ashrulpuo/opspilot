/**
 * Encryption Store - manages client-side encryption state
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface EncryptionState {
  masterPassword: string | null
  isUnlocked: boolean
  testEncrypted: string | null
  testNonce: string | null
  testSalt: string | null
}

export const useEncryptionStore = defineStore(
  'encryption',
  () => {
    // State
    const masterPassword = ref<string | null>(null)
    const isUnlocked = ref(false)
    const testEncrypted = ref<string | null>(null)
    const testNonce = ref<string | null>(null)
    const testSalt = ref<string | null>(null)

    // Computed
    const hasMasterPassword = computed(() => {
      return !!localStorage.getItem('opspilot_encryption_config')
    })

    // Actions
    async function setMasterPassword(password: string): Promise<void> {
      const { getEncryptionService } = await import('@/services/encryption/encryption.service')
      const encryptionService = await getEncryptionService()

      const testValue = await encryptionService.generateTestValue(password)

      // Store encrypted test values in localStorage
      const config = {
        testEncrypted: testValue.encrypted_test,
        testNonce: testValue.nonce,
        testSalt: testValue.salt,
      }

      localStorage.setItem('opspilot_encryption_config', JSON.stringify(config))

      // Keep in memory for current session
      masterPassword.value = password
      testEncrypted.value = testValue.encrypted_test
      testNonce.value = testValue.nonce
      testSalt.value = testValue.salt
      isUnlocked.value = true
    }

    async function verifyPassword(password: string): Promise<boolean> {
      const configStr = localStorage.getItem('opspilot_encryption_config')
      if (!configStr) return false

      const config = JSON.parse(configStr)

      try {
        const { getEncryptionService } = await import('@/services/encryption/encryption.service')
        const encryptionService = await getEncryptionService()

        const isValid = await encryptionService.verifyPassword(
          config.testEncrypted,
          config.testNonce,
          config.testSalt,
          password
        )

        if (isValid) {
          masterPassword.value = password
          testEncrypted.value = config.testEncrypted
          testNonce.value = config.testNonce
          testSalt.value = config.testSalt
          isUnlocked.value = true
        }

        return isValid
      } catch (error) {
        return false
      }
    }

    function lock(): void {
      masterPassword.value = null
      isUnlocked.value = false
      testEncrypted.value = null
      testNonce.value = null
      testSalt.value = null
    }

    function clearMasterPassword(): void {
      lock()
      localStorage.removeItem('opspilot_encryption_config')
    }

    return {
      // State
      masterPassword,
      isUnlocked,
      testEncrypted,
      testNonce,
      testSalt,
      // Computed
      hasMasterPassword,
      // Actions
      setMasterPassword,
      verifyPassword,
      lock,
      clearMasterPassword,
    }
  },
  {
    persist: false, // Don't persist the master password itself!
  }
)

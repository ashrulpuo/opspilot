/**
 * Composable for credential encryption operations
 */

import { ref, computed } from 'vue'
import { useEncryptionStore } from '@/stores/modules/encryption'
import { getEncryptionService } from '@/services/encryption/encryption.service'

export function useCredentialEncryption() {
  const encryptionStore = useEncryptionStore()
  const encrypting = ref(false)
  const decrypting = ref(false)

  const isEncryptionAvailable = computed(() => {
    return encryptionStore.isUnlocked && encryptionStore.masterPassword
  })

  /**
   * Encrypt credential data before sending to backend
   */
  async function encryptCredentialData(data: Record<string, any>) {
    if (!isEncryptionAvailable.value) {
      throw new Error('Encryption not available. Please unlock credentials first.')
    }

    encrypting.value = true

    try {
      const encryptionService = await getEncryptionService()
      const encrypted = await encryptionService.encryptCredentialData(data, encryptionStore.masterPassword!)

      return encrypted
    } finally {
      encrypting.value = false
    }
  }

  /**
   * Decrypt credential data for viewing
   */
  async function decryptCredentialData(encryptedData: string, nonce: string, salt: string) {
    if (!isEncryptionAvailable.value) {
      throw new Error('Encryption not available. Please unlock credentials first.')
    }

    decrypting.value = true

    try {
      const encryptionService = await getEncryptionService()
      const decrypted = await encryptionService.decryptCredentialData(
        encryptedData,
        nonce,
        salt,
        encryptionStore.masterPassword!
      )

      return decrypted
    } finally {
      decrypting.value = false
    }
  }

  /**
   * Check if credential data needs to be shown encrypted
   */
  function shouldShowEncrypted(credential: any) {
    return credential.encrypted_data && credential.nonce && credential.salt && !isEncryptionAvailable.value
  }

  /**
   * Prepare credential form data with encryption
   */
  async function prepareCredentialFormData(formData: Record<string, any>) {
    // Remove sensitive fields from plain data
    const plainData = { ...formData }
    delete plainData.password
    delete plainData.api_key
    delete plainData.token
    delete plainData.private_key

    // Extract sensitive fields for encryption
    const sensitiveData: Record<string, any> = {}
    if (formData.password) sensitiveData.password = formData.password
    if (formData.api_key) sensitiveData.api_key = formData.api_key
    if (formData.token) sensitiveData.token = formData.token
    if (formData.private_key) sensitiveData.private_key = formData.private_key

    // Encrypt sensitive data
    const encrypted = await encryptCredentialData(sensitiveData)

    return {
      ...plainData,
      encrypted_data: encrypted.encrypted_data,
      nonce: encrypted.nonce,
      salt: encrypted.salt,
    }
  }

  return {
    // State
    encrypting,
    decrypting,
    isEncryptionAvailable,
    // Methods
    encryptCredentialData,
    decryptCredentialData,
    shouldShowEncrypted,
    prepareCredentialFormData,
  }
}

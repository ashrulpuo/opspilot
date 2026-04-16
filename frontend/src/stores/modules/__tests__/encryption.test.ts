/**
 * Encryption Store Unit Tests
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useEncryptionStore } from '../encryption'

describe('Encryption Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('Master Password Setup', () => {
    it('should set master password and store encrypted config', async () => {
      const store = useEncryptionStore()
      const password = 'master-password-123'

      await store.setMasterPassword(password)

      expect(store.masterPassword).toBe(password)
      expect(store.isUnlocked).toBe(true)
      expect(store.hasMasterPassword).toBe(true)
      expect(localStorage.getItem('opspilot_encryption_config')).toBeTruthy()
    })

    it('should store test values for verification', async () => {
      const store = useEncryptionStore()
      const password = 'master-password-123'

      await store.setMasterPassword(password)

      expect(store.testEncrypted).toBeTruthy()
      expect(store.testNonce).toBeTruthy()
      expect(store.testSalt).toBeTruthy()
    })

    it('should not store plain password in localStorage', async () => {
      const store = useEncryptionStore()
      const password = 'master-password-123'

      await store.setMasterPassword(password)

      const config = JSON.parse(localStorage.getItem('opspilot_encryption_config')!)

      expect(config.password).toBeUndefined()
      expect(config.testEncrypted).toBeTruthy()
      expect(config.testNonce).toBeTruthy()
      expect(config.testSalt).toBeTruthy()
    })
  })

  describe('Password Verification', () => {
    it('should verify correct password', async () => {
      const store = useEncryptionStore()
      const password = 'master-password-123'

      await store.setMasterPassword(password)
      store.lock() // Lock after setup

      const isValid = await store.verifyPassword(password)

      expect(isValid).toBe(true)
      expect(store.isUnlocked).toBe(true)
      expect(store.masterPassword).toBe(password)
    })

    it('should reject incorrect password', async () => {
      const store = useEncryptionStore()
      const password = 'master-password-123'
      const wrongPassword = 'wrong-password'

      await store.setMasterPassword(password)
      store.lock() // Lock after setup

      const isValid = await store.verifyPassword(wrongPassword)

      expect(isValid).toBe(false)
      expect(store.isUnlocked).toBe(false)
      expect(store.masterPassword).toBeNull()
    })

    it('should return false when no master password is set', async () => {
      const store = useEncryptionStore()

      const isValid = await store.verifyPassword('any-password')

      expect(isValid).toBe(false)
    })
  })

  describe('Lock/Unlock State', () => {
    it('should lock and clear password from memory', async () => {
      const store = useEncryptionStore()
      const password = 'master-password-123'

      await store.setMasterPassword(password)
      expect(store.isUnlocked).toBe(true)

      store.lock()

      expect(store.isUnlocked).toBe(false)
      expect(store.masterPassword).toBeNull()
      expect(store.testEncrypted).toBeNull()
      expect(store.testNonce).toBeNull()
      expect(store.testSalt).toBeNull()
    })

    it('should keep config in localStorage after lock', async () => {
      const store = useEncryptionStore()
      const password = 'master-password-123'

      await store.setMasterPassword(password)
      store.lock()

      expect(store.hasMasterPassword).toBe(true)
      expect(localStorage.getItem('opspilot_encryption_config')).toBeTruthy()
    })

    it('should unlock after setting master password', async () => {
      const store = useEncryptionStore()
      const password = 'master-password-123'

      expect(store.isUnlocked).toBe(false)

      await store.setMasterPassword(password)

      expect(store.isUnlocked).toBe(true)
    })

    it('should unlock after verifying password', async () => {
      const store = useEncryptionStore()
      const password = 'master-password-123'

      await store.setMasterPassword(password)
      store.lock()
      expect(store.isUnlocked).toBe(false)

      await store.verifyPassword(password)

      expect(store.isUnlocked).toBe(true)
    })
  })

  describe('Clear Master Password', () => {
    it('should clear master password completely', async () => {
      const store = useEncryptionStore()
      const password = 'master-password-123'

      await store.setMasterPassword(password)
      expect(store.hasMasterPassword).toBe(true)

      store.clearMasterPassword()

      expect(store.hasMasterPassword).toBe(false)
      expect(store.isUnlocked).toBe(false)
      expect(store.masterPassword).toBeNull()
      expect(localStorage.getItem('opspilot_encryption_config')).toBeNull()
    })

    it('should lock when clearing master password', async () => {
      const store = useEncryptionStore()
      const password = 'master-password-123'

      await store.setMasterPassword(password)
      expect(store.isUnlocked).toBe(true)

      store.clearMasterPassword()

      expect(store.isUnlocked).toBe(false)
    })
  })

  describe('Computed Properties', () => {
    it('hasMasterPassword should be false when not set', () => {
      const store = useEncryptionStore()

      expect(store.hasMasterPassword).toBe(false)
    })

    it('hasMasterPassword should be true when set', async () => {
      const store = useEncryptionStore()
      const password = 'master-password-123'

      await store.setMasterPassword(password)

      expect(store.hasMasterPassword).toBe(true)
    })

    it('hasMasterPassword should be true even when locked', async () => {
      const store = useEncryptionStore()
      const password = 'master-password-123'

      await store.setMasterPassword(password)
      store.lock()

      expect(store.hasMasterPassword).toBe(true)
    })

    it('isUnlocked should be false initially', () => {
      const store = useEncryptionStore()

      expect(store.isUnlocked).toBe(false)
    })

    it('isUnlocked should be true after setting password', async () => {
      const store = useEncryptionStore()
      const password = 'master-password-123'

      await store.setMasterPassword(password)

      expect(store.isUnlocked).toBe(true)
    })
  })

  describe('Multiple Setup Attempts', () => {
    it('should allow setting master password multiple times', async () => {
      const store = useEncryptionStore()
      const password1 = 'password-123'
      const password2 = 'password-456'

      await store.setMasterPassword(password1)
      const config1 = JSON.parse(localStorage.getItem('opspilot_encryption_config')!)

      await store.setMasterPassword(password2)
      const config2 = JSON.parse(localStorage.getItem('opspilot_encryption_config')!)

      expect(store.masterPassword).toBe(password2)
      expect(config1.testEncrypted).not.toBe(config2.testEncrypted)
    })

    it('should verify with latest password after re-setting', async () => {
      const store = useEncryptionStore()
      const password1 = 'password-123'
      const password2 = 'password-456'

      await store.setMasterPassword(password1)
      store.lock()

      const isValid1 = await store.verifyPassword(password1)
      expect(isValid1).toBe(true)

      await store.setMasterPassword(password2)
      store.lock()

      const isValid2 = await store.verifyPassword(password1)
      expect(isValid2).toBe(false)

      const isValid3 = await store.verifyPassword(password2)
      expect(isValid3).toBe(true)
    })
  })
})

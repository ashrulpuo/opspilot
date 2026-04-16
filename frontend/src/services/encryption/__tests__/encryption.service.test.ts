/**
 * Encryption Service Unit Tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { EncryptionService } from '../encryption.service'

describe('EncryptionService', () => {
  let encryptionService: EncryptionService

  beforeEach(async () => {
    encryptionService = await EncryptionService.getInstance()
  })

  describe('Key Derivation', () => {
    it('should derive the same key from the same password and salt', async () => {
      const password = 'test-password-123'
      const salt = encryptionService.generateSalt()

      const key1 = await encryptionService.deriveKey(password, salt)
      const key2 = await encryptionService.deriveKey(password, salt)

      expect(key1).toEqual(key2)
    })

    it('should derive different keys from different passwords', async () => {
      const salt = encryptionService.generateSalt()

      const key1 = await encryptionService.deriveKey('password1', salt)
      const key2 = await encryptionService.deriveKey('password2', salt)

      expect(key1).not.toEqual(key2)
    })

    it('should derive different keys from different salts', async () => {
      const password = 'test-password'
      const salt1 = encryptionService.generateSalt()
      const salt2 = encryptionService.generateSalt()

      const key1 = await encryptionService.deriveKey(password, salt1)
      const key2 = await encryptionService.deriveKey(password, salt2)

      expect(key1).not.toEqual(key2)
    })

    it('should generate unique salts', () => {
      const salt1 = encryptionService.generateSalt()
      const salt2 = encryptionService.generateSalt()

      expect(salt1).not.toBe(salt2)
      expect(salt1.length).toBeGreaterThan(0)
      expect(salt2.length).toBeGreaterThan(0)
    })
  })

  describe('Encryption/Decryption', () => {
    it('should encrypt and decrypt a simple string', async () => {
      const password = 'master-password-123'
      const data = 'secret credential data'

      const encrypted = await encryptionService.encrypt(data, password)
      const decrypted = await encryptionService.decrypt(
        encrypted.encryptedData,
        encrypted.nonce,
        password,
        encryptionService.generateSalt()
      )

      expect(decrypted).toBe(data)
    })

    it('should produce different encrypted data for the same input', async () => {
      const password = 'master-password-123'
      const data = 'secret credential data'
      const salt = encryptionService.generateSalt()

      const encrypted1 = await encryptionService.encrypt(data, password, salt)
      const encrypted2 = await encryptionService.encrypt(data, password, salt)

      expect(encrypted1.encryptedData).not.toBe(encrypted2.encryptedData)
      expect(encrypted1.nonce).not.toBe(encrypted2.nonce)
    })

    it('should fail to decrypt with wrong password', async () => {
      const password = 'master-password-123'
      const wrongPassword = 'wrong-password'
      const data = 'secret credential data'

      const encrypted = await encryptionService.encrypt(data, password)

      await expect(
        encryptionService.decrypt(
          encrypted.encryptedData,
          encrypted.nonce,
          wrongPassword,
          encryptionService.generateSalt()
        )
      ).rejects.toThrow()
    })

    it('should encrypt and decrypt JSON objects', async () => {
      const password = 'master-password-123'
      const data = {
        username: 'admin',
        password: 'secret123',
        apiKey: 'api-key-12345',
      }

      const encrypted = await encryptionService.encryptCredentialData(data, password)
      const decrypted = await encryptionService.decryptCredentialData(
        encrypted.encrypted_data,
        encrypted.nonce,
        encrypted.salt,
        password
      )

      expect(decrypted).toEqual(data)
    })

    it('should handle complex credential data', async () => {
      const password = 'master-password-123'
      const data = {
        type: 'ssh_key',
        username: 'deploy',
        private_key: '-----BEGIN RSA PRIVATE KEY-----\ntest key data\n-----END RSA PRIVATE KEY-----',
        passphrase: 'ssh-passphrase',
        port: 22,
      }

      const encrypted = await encryptionService.encryptCredentialData(data, password)
      const decrypted = await encryptionService.decryptCredentialData(
        encrypted.encrypted_data,
        encrypted.nonce,
        encrypted.salt,
        password
      )

      expect(decrypted).toEqual(data)
    })
  })

  describe('Password Verification', () => {
    it('should verify correct password', async () => {
      const password = 'master-password-123'
      const testValue = await encryptionService.generateTestValue(password)

      const isValid = await encryptionService.verifyPassword(
        testValue.encrypted_test,
        testValue.nonce,
        testValue.salt,
        password
      )

      expect(isValid).toBe(true)
    })

    it('should reject incorrect password', async () => {
      const password = 'master-password-123'
      const wrongPassword = 'wrong-password'
      const testValue = await encryptionService.generateTestValue(password)

      const isValid = await encryptionService.verifyPassword(
        testValue.encrypted_test,
        testValue.nonce,
        testValue.salt,
        wrongPassword
      )

      expect(isValid).toBe(false)
    })

    it('should generate consistent test values', async () => {
      const password = 'master-password-123'
      const testValue = await encryptionService.generateTestValue(password)

      expect(testValue.encrypted_test).toBeTruthy()
      expect(testValue.nonce).toBeTruthy()
      expect(testValue.salt).toBeTruthy()

      const isValid1 = await encryptionService.verifyPassword(
        testValue.encrypted_test,
        testValue.nonce,
        testValue.salt,
        password
      )

      const isValid2 = await encryptionService.verifyPassword(
        testValue.encrypted_test,
        testValue.nonce,
        testValue.salt,
        password
      )

      expect(isValid1).toBe(true)
      expect(isValid2).toBe(true)
    })
  })

  describe('Edge Cases', () => {
    it('should handle empty strings', async () => {
      const password = 'master-password-123'
      const data = ''

      const encrypted = await encryptionService.encrypt(data, password)
      const decrypted = await encryptionService.decrypt(
        encrypted.encryptedData,
        encrypted.nonce,
        password,
        encryptionService.generateSalt()
      )

      expect(decrypted).toBe('')
    })

    it('should handle special characters', async () => {
      const password = 'master-password-123!@#$%'
      const data = 'secret-data-áéíóú-cjk-emoji-😀'

      const encrypted = await encryptionService.encrypt(data, password)
      const decrypted = await encryptionService.decrypt(
        encrypted.encryptedData,
        encrypted.nonce,
        password,
        encryptionService.generateSalt()
      )

      expect(decrypted).toBe(data)
    })

    it('should handle very long passwords', async () => {
      const password = 'a'.repeat(1000)
      const data = 'test data'

      const encrypted = await encryptionService.encrypt(data, password)
      const decrypted = await encryptionService.decrypt(
        encrypted.encryptedData,
        encrypted.nonce,
        password,
        encryptionService.generateSalt()
      )

      expect(decrypted).toBe(data)
    })

    it('should handle very long data', async () => {
      const password = 'master-password-123'
      const data = 'a'.repeat(10000)

      const encrypted = await encryptionService.encrypt(data, password)
      const decrypted = await encryptionService.decrypt(
        encrypted.encryptedData,
        encrypted.nonce,
        password,
        encryptionService.generateSalt()
      )

      expect(decrypted).toBe(data)
    })
  })

  describe('Singleton Pattern', () => {
    it('should return the same instance', async () => {
      const instance1 = await EncryptionService.getInstance()
      const instance2 = await EncryptionService.getInstance()

      expect(instance1).toBe(instance2)
    })
  })
})

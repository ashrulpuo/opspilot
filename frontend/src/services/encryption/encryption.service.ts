/**
 * Encryption Service using libsodium-wrappers
 * Client-side encryption for credentials
 */

import _sodium from 'libsodium-wrappers'

export interface EncryptionResult {
  encryptedData: string
  nonce: string
}

export class EncryptionService {
  private sodium: any
  private ready: boolean = false
  private static instance: EncryptionService

  private constructor() {}

  public static async getInstance(): Promise<EncryptionService> {
    if (!EncryptionService.instance) {
      EncryptionService.instance = new EncryptionService()
      await EncryptionService.instance.initialize()
    }
    return EncryptionService.instance
  }

  private async initialize(): Promise<void> {
    if (!this.ready) {
      // Import libsodium-wrappers properly
      this.sodium = await _sodium
      await this.sodium.ready
      this.ready = true
    }
  }

  /**
   * Derive encryption key from master password using Argon2id
   */
  public async deriveKey(password: string, salt: string): Promise<Uint8Array> {
    if (!this.ready) await this.initialize()

    const saltBuffer = this.sodium.from_hex(salt)
    const key = this.sodium.crypto_pwhash(
      this.sodium.crypto_secretbox_KEYBYTES,
      password,
      saltBuffer,
      this.sodium.crypto_pwhash_OPSLIMIT_MODERATE,
      this.sodium.crypto_pwhash_MEMLIMIT_MODERATE,
      this.sodium.crypto_pwhash_ALG_ARGON2ID13
    )
    return key
  }

  /**
   * Generate random salt for key derivation
   */
  public generateSalt(): string {
    if (!this.ready) this.initialize()

    const salt = this.sodium.randombytes_buf(this.sodium.crypto_pwhash_SALTBYTES)
    return this.sodium.to_hex(salt)
  }

  /**
   * Encrypt data using master password-derived key
   */
  public async encrypt(data: string, password: string, salt?: string): Promise<EncryptionResult> {
    if (!this.ready) await this.initialize()

    const encryptionSalt = salt || this.generateSalt()
    const key = await this.deriveKey(password, encryptionSalt)
    const nonce = this.sodium.randombytes_buf(this.sodium.crypto_secretbox_NONCEBYTES)

    const encrypted = this.sodium.crypto_secretbox_easy(data, nonce, key)

    return {
      encryptedData: this.sodium.to_base64(encrypted),
      nonce: this.sodium.to_hex(nonce),
    }
  }

  /**
   * Decrypt data using master password-derived key
   */
  public async decrypt(encryptedData: string, nonce: string, password: string, salt: string): Promise<string> {
    if (!this.ready) await this.initialize()

    const key = await this.deriveKey(password, salt)
    const nonceBuffer = this.sodium.from_hex(nonce)
    const encryptedBuffer = this.sodium.from_base64(encryptedData, this.sodium.base64_variants.ORIGINAL)

    const decrypted = this.sodium.crypto_secretbox_open_easy(encryptedBuffer, nonceBuffer, key)

    return this.sodium.to_string(decrypted)
  }

  /**
   * Encrypt credential data for storage
   */
  public async encryptCredentialData(
    data: Record<string, any>,
    password: string
  ): Promise<{
    encrypted_data: string
    nonce: string
    salt: string
  }> {
    const salt = this.generateSalt()
    const dataString = JSON.stringify(data)
    const result = await this.encrypt(dataString, password, salt)

    return {
      encrypted_data: result.encryptedData,
      nonce: result.nonce,
      salt: salt,
    }
  }

  /**
   * Decrypt credential data for viewing
   */
  public async decryptCredentialData(
    encryptedData: string,
    nonce: string,
    salt: string,
    password: string
  ): Promise<Record<string, any>> {
    const decryptedString = await this.decrypt(encryptedData, nonce, password, salt)
    return JSON.parse(decryptedString)
  }

  /**
   * Verify master password by attempting to decrypt a known value
   */
  public async verifyPassword(encryptedTest: string, nonce: string, salt: string, password: string): Promise<boolean> {
    try {
      await this.decrypt(encryptedTest, nonce, password, salt)
      return true
    } catch (error) {
      return false
    }
  }

  /**
   * Generate test value for password verification
   */
  public async generateTestValue(password: string): Promise<{
    encrypted_test: string
    nonce: string
    salt: string
  }> {
    const testValue = 'VALID_PASSWORD'
    const salt = this.generateSalt()
    const result = await this.encrypt(testValue, password, salt)

    return {
      encrypted_test: result.encryptedData,
      nonce: result.nonce,
      salt: salt,
    }
  }
}

// Singleton instance
let encryptionServiceInstance: EncryptionService | null = null

export async function getEncryptionService(): Promise<EncryptionService> {
  if (!encryptionServiceInstance) {
    encryptionServiceInstance = await EncryptionService.getInstance()
  }
  return encryptionServiceInstance
}

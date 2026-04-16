# Client-Side Credential Encryption

## Overview

OpsPilot now supports client-side encryption for sensitive credential data. This ensures that passwords, API keys, tokens, and SSH keys are encrypted in the browser before being sent to the server, and only decrypted when viewed by authorized users.

## Architecture

### Encryption Flow

1. **Master Password Setup**
   - User creates a master password (minimum 12 characters, recommended strong password)
   - Master password is used to derive an encryption key using Argon2id KDF
   - A test value is encrypted and stored in localStorage for password verification
   - Master password is NEVER stored in plain text - only kept in memory during session

2. **Credential Encryption**
   - When creating/updating credentials, sensitive fields are encrypted client-side
   - Encrypted data includes: `encrypted_data`, `nonce`, `salt`
   - Backend stores encrypted data without access to plain text

3. **Credential Decryption**
   - When viewing credentials, user must unlock with master password
   - Encrypted data is decrypted client-side using the master password
   - Plain text is only shown in the browser briefly

### Security Features

- **Zero-Knowledge Architecture**: Server never sees plain text credentials
- **Argon2id KDF**: Industry-standard password-based key derivation
- **libsodium-wrappers**: Battle-tested cryptographic library
- **Unique Nonces**: Each encryption uses a random nonce
- **Session-Based**: Master password only kept in memory during session
- **Auto-Lock**: Credentials lock automatically when needed

## Components

### 1. Encryption Service

**Location**: `src/services/encryption/encryption.service.ts`

Provides core encryption/decryption functionality using libsodium-wrappers.

```typescript
import { getEncryptionService } from '@/services/encryption/encryption.service';

const encryptionService = await getEncryptionService();

// Encrypt credential data
const encrypted = await encryptionService.encryptCredentialData(
  { password: 'secret123' },
  masterPassword
);

// Decrypt credential data
const decrypted = await encryptionService.decryptCredentialData(
  encrypted.encrypted_data,
  encrypted.nonce,
  encrypted.salt,
  masterPassword
);
```

### 2. Encryption Store

**Location**: `src/stores/modules/encryption.ts`

Pinia store managing encryption state and master password.

```typescript
import { useEncryptionStore } from '@/stores/modules/encryption';

const encryptionStore = useEncryptionStore();

// Check if master password is set
if (encryptionStore.hasMasterPassword) {
  // Unlock credentials
  await encryptionStore.verifyPassword(password);
} else {
  // Setup new master password
  await encryptionStore.setMasterPassword(password);
}

// Lock credentials (clear from memory)
encryptionStore.lock();

// Clear master password completely
encryptionStore.clearMasterPassword();
```

### 3. Master Password Setup Modal

**Location**: `src/components/encryption/MasterPasswordSetupModal.vue`

Modal component for setting up initial master password.

Features:
- Password strength indicator (Weak/Fair/Good/Strong)
- Password confirmation
- Minimum 12 character requirement
- Warning about password recovery impossibility

### 4. Master Password Unlock Modal

**Location**: `src/components/encryption/MasterPasswordUnlockModal.vue`

Modal component for unlocking credentials with master password.

Features:
- Simple password input
- Clear error messages for incorrect passwords
- Auto-focus on password field

### 5. Credential Encryption Composable

**Location**: `src/composables/useCredentialEncryption.ts`

Composable for handling encryption in credential forms.

```typescript
import { useCredentialEncryption } from '@/composables/useCredentialEncryption';

const {
  encrypting,
  decrypting,
  isEncryptionAvailable,
  encryptCredentialData,
  decryptCredentialData,
  prepareCredentialFormData
} = useCredentialEncryption();

// Encrypt credential before sending to backend
const encrypted = await encryptCredentialData({
  username: 'admin',
  password: 'secret123'
});

// Decrypt credential for viewing
const decrypted = await decryptCredentialData(
  credential.encrypted_data,
  credential.nonce,
  credential.salt
);

// Prepare form data with encryption
const formData = await prepareCredentialFormData({
  name: 'Database Credential',
  username: 'admin',
  password: 'secret123',
  description: 'Production database'
});
```

## Usage Guide

### Setting Up Encryption

1. **First-Time Setup**
   ```vue
   <template>
     <MasterPasswordSetupModal
       v-model="showSetupModal"
       @success="onSetupSuccess"
     />
   </template>

   <script setup lang="ts">
   import { ref } from 'vue';
   import MasterPasswordSetupModal from '@/components/encryption/MasterPasswordSetupModal.vue';

   const showSetupModal = ref(true);

   function onSetupSuccess() {
     console.log('Encryption setup complete');
   }
   </script>
   ```

2. **Unlocking Credentials**
   ```vue
   <template>
     <MasterPasswordUnlockModal
       v-model="showUnlockModal"
       @success="onUnlockSuccess"
     />
   </template>

   <script setup lang="ts">
   import { ref } from 'vue';
   import MasterPasswordUnlockModal from '@/components/encryption/MasterPasswordUnlockModal.vue';

   const showUnlockModal = ref(false);

   function showUnlock() {
     showUnlockModal.value = true;
   }

   function onUnlockSuccess() {
     console.log('Credentials unlocked');
   }
   </script>
   ```

### Creating Encrypted Credentials

```vue
<script setup lang="ts">
import { ref } from 'vue';
import { useCredentialEncryption } from '@/composables/useCredentialEncryption';
import { CredentialsAPI } from '@/api/opspilot/credentials';

const { prepareCredentialFormData, isEncryptionAvailable } = useCredentialEncryption();

const form = ref({
  name: 'Production Database',
  type: 'password',
  username: 'admin',
  password: 'secret123',
  server_id: 'server-123'
});

async function submitCredential() {
  if (!isEncryptionAvailable.value) {
    // Show unlock modal
    return;
  }

  const formData = await prepareCredentialFormData(form.value);
  
  await CredentialsAPI.create('org-123', formData);
}
</script>
```

### Viewing Encrypted Credentials

```vue
<script setup lang="ts">
import { ref } from 'vue';
import { useCredentialEncryption } from '@/composables/useCredentialEncryption';
import { CredentialsAPI } from '@/api/opspilot/credentials';

const { decryptCredentialData, isEncryptionAvailable } = useCredentialEncryption();

const credentials = ref([]);
const decryptedCredentials = ref(new Map());

async function loadCredentials() {
  const response = await CredentialsAPI.list();
  credentials.value = response.items;
}

async function decryptCredential(credential: any) {
  if (!isEncryptionAvailable.value) {
    // Show unlock modal
    return;
  }

  const decrypted = await decryptCredentialData(
    credential.encrypted_data,
    credential.nonce,
    credential.salt
  );

  decryptedCredentials.value.set(credential.id, decrypted);
}
</script>

<template>
  <div v-for="cred in credentials" :key="cred.id">
    <h3>{{ cred.name }}</h3>
    <button @click="decryptCredential(cred)">View Details</button>
    
    <div v-if="decryptedCredentials.get(cred.id)">
      <p>Username: {{ decryptedCredentials.get(cred.id).username }}</p>
      <p>Password: {{ decryptedCredentials.get(cred.id).password }}</p>
    </div>
  </div>
</template>
```

## API Changes

### Credential Types

```typescript
export interface Credential {
  id: string;
  server_id: string;
  name: string;
  type: 'ssh_key' | 'password' | 'api_key' | 'token';
  description?: string;
  
  // Encryption fields
  encrypted_data?: string;
  nonce?: string;
  salt?: string;
  
  created_at: string;
  updated_at: string;
}

export interface CreateCredentialRequest {
  server_id: string;
  name: string;
  type: 'ssh_key' | 'password' | 'api_key' | 'token';
  data?: Record<string, any>;        // Legacy: plain data
  encrypted_data?: string;            // New: encrypted data
  nonce?: string;                     // New: encryption nonce
  salt?: string;                      // New: encryption salt
  description?: string;
}
```

## Testing

### Run Unit Tests

```bash
# Run all tests
pnpm test:unit

# Run coverage
pnpm test:coverage

# Run specific test file
pnpm test:unit encryption.service.test.ts
```

### Test Files

- `src/services/encryption/__tests__/encryption.service.test.ts` - Encryption service tests
- `src/stores/modules/__tests__/encryption.test.ts` - Encryption store tests

## Security Best Practices

### For Users

1. **Use Strong Master Passwords**
   - Minimum 12 characters
   - Mix of uppercase, lowercase, numbers, and symbols
   - Avoid common words or patterns

2. **Store Master Password Securely**
   - Use a password manager (1Password, Bitwarden, etc.)
   - Never write it down or share it
   - Remember: It cannot be recovered!

3. **Lock When Away**
   - Use auto-lock features
   - Lock manually when stepping away
   - Close browser tabs when done

4. **Verify Encryption**
   - Check that credentials are encrypted before sending
   - Look for encrypted indicators in the UI
   - Report any suspicious behavior

### For Developers

1. **Never Store Plain Text**
   - Always encrypt sensitive data before sending
   - Never log or debug plain text credentials
   - Use encryption composable for all credential operations

2. **Validate Encryption State**
   - Check `isEncryptionAvailable` before operations
   - Show unlock modal when locked
   - Handle encryption errors gracefully

3. **Clear Sensitive Data**
   - Clear decrypted data after use
   - Don't store decrypted data in component state
   - Use auto-clear mechanisms

4. **Test Thoroughly**
   - Test encryption/decryption flows
   - Test error cases (wrong password, locked state)
   - Test edge cases (empty strings, special characters)

## Troubleshooting

### Common Issues

**Issue: Can't access encrypted credentials**
- Solution: Verify master password is correct
- Solution: Check that encryption is unlocked
- Solution: Clear localStorage and set up again (WARNING: This loses all credentials!)

**Issue: Encryption fails**
- Solution: Ensure libsodium-wrappers is loaded
- Solution: Check browser compatibility
- Solution: Verify encryption service is initialized

**Issue: Decryption fails**
- Solution: Verify master password is correct
- Solution: Check nonce and salt values
- Solution: Ensure data wasn't corrupted

**Issue: Lost Master Password**
- WARNING: Cannot be recovered!
- Solution: Clear master password and set up new one
- WARNING: All existing encrypted credentials will be inaccessible!

## Browser Compatibility

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Opera 76+

Required features:
- Web Crypto API (supported by libsodium-wrappers)
- localStorage
- ES6+ (async/await, Promises)

## Migration Guide

### Migrating from Plain Text Credentials

1. **Setup Encryption**
   - Deploy new frontend code
   - Users will be prompted to set up master password

2. **Migrate Existing Credentials**
   - Backend migration script to encrypt existing credentials
   - Or: Users re-enter credentials with new encryption

3. **Phase Out Plain Text**
   - Deprecate `data` field in CreateCredentialRequest
   - Remove plain text credential support after migration

## Future Enhancements

- [ ] Biometric unlock (WebAuthn)
- [ ] Password sharing between team members
- [ ] Credential rotation automation
- [ ] Backup/restore master password (encrypted)
- [ ] Multi-factor authentication for unlock
- [ ] Audit log for credential access
- [ ] Temporary access tokens
- [ ] Credential templates

## Support

For issues or questions:
- Create an issue in the repository
- Contact the security team for security concerns
- Review security documentation

## License

This encryption implementation is part of OpsPilot and follows the same license.

import { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Starting E2E test teardown...');
  
  // Clean up test data
  console.log('🗑️ Cleaning up test data...');
  await cleanupTestData();
  
  // Clean up test reports if needed
  // await cleanupTestReports();
  
  console.log('✅ E2E test teardown complete');
}

async function cleanupTestData() {
  // Here you can add code to clean up test data via API
  // For example, delete test users, servers, etc.
  
  // Example:
  // const response = await fetch('http://localhost:8000/api/v1/test/cleanup', {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  // });
  
  console.log('✅ Test data cleaned up');
}

export default globalTeardown;
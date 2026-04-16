import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting E2E test setup...');
  
  const baseURL = config.projects?.[0]?.use?.baseURL || 'http://localhost:5173';
  
  // Wait for server to be ready
  console.log(`⏳ Waiting for server at ${baseURL}...`);
  
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  let retries = 30;
  let isReady = false;
  
  while (retries > 0 && !isReady) {
    try {
      await page.goto(baseURL, { timeout: 5000 });
      isReady = true;
      console.log('✅ Server is ready');
    } catch (error) {
      retries--;
      if (retries === 0) {
        throw new Error(`Server not ready after 30 attempts: ${error}`);
      }
      console.log(`⏳ Server not ready yet, retrying... (${retries} attempts left)`);
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
  
  await context.close();
  await browser.close();
  
  // Seed test data
  console.log('📊 Seeding test data...');
  await seedTestData();
  
  console.log('✅ E2E test setup complete');
}

async function seedTestData() {
  // Here you can add code to seed test data via API
  // For example, create test users, servers, etc.
  
  // Example:
  // const response = await fetch('http://localhost:8000/api/v1/test/seed', {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  // });
  
  console.log('✅ Test data seeded');
}

export default globalSetup;
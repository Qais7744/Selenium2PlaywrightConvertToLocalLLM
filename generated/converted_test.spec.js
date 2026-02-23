const { test, expect } = require('@playwright/test');

test.describe('TestSuite', () => {
    test('loginTest', async ({ page }) => {
        await page.goto("https://example.com/login");
        
        // Find elements and interact
        await page.locator("#username").fill("testuser");
        await page.locator("#password").fill("password123");
        await page.locator("button[type='submit']").click();
        
        // Assertion
        expect(await page.title()).toContain("Dashboard");
        driver.quit();
    });
});
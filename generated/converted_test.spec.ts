(async () => {
  const { chromium } = require('playwright');

  // Create a new Chromium browser instance
  const browser = await chromium.launch();

  // Open a new page in the browser
  const page = await browser.newPage();

  try {
    // Navigate to Google
    await page.goto("https://www.google.com");

    // Print the title of the page
    console.log(await page.title());
  } finally {
    // Close the browser
    await browser.close();
  }
})();
# Findings Log

## Research & Discoveries

### TestNG to Playwright Typescript Mapping

| TestNG Concept | Playwright TS Equivalent | Notes |
| :--- | :--- | :--- |
| `@Test` | `test('name', async ({ page }) => { ... })` | Direct mapping. |
| `@BeforeMethod` | `test.beforeEach(({ page }) => { ... })` | Runs before every test in the file/describe block. |
| `@AfterMethod` | `test.afterEach(({ page }) => { ... })` | Cleanup after every test. |
| `@BeforeClass` | `test.beforeAll(async () => { ... })` | Runs once before all tests in the file/describe block. |
| `@AfterClass` | `test.afterAll(async () => { ... })` | Runs once after all tests. |
| `@DataProvider` | `[data].forEach(data => test(..., () => ...))` | Use JS/TS loops to generate tests dynamically. |
| `Assert.assertEquals` | `expect(actual).toBe(expected)` | Playwright uses Jest-like `expect` assertions. |
| `Assert.assertTrue` | `expect(actual).toBeTruthy()` | |
| `driver.findElement(By.id("..."))` | `page.locator('#...')` | Playwright Use Locators (CSS/XPath/Text). |
| `element.click()` | `await locator.click()` | **Async/Await is mandatory**. |

## Constraints
> [!IMPORTANT]
> 1.  **Async/Await**: Java is synchronous; Playwright TS is asynchronous. Conversion MUST inject `await` keywords.
> 2.  **Locators**: Selenium `By.` strategies need to be converted to Playwright `locator()`.
> 3.  **Browser Management**: Selenium `driver` setup is replaced by Playwright's auto-managed `page` fixture. Do not port `new ChromeDriver()` calls.

## Integration Architecture
- **Frontend**: Simple HTML/CSS/JS Dashboard.
- **Backend**: Python (Flask) to handle "Text Processing" and "File I/O".
- **AI Engine**: Local LLM (Ollama/LlamaCpp) or Cloud API (Gemini/OpenAI) prompts based on the Mapping Table.

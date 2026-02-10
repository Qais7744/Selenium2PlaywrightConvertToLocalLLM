# Conversion SOP (Standard Operating Procedure)

## Goal
Convert Selenium Java (TestNG) code into idiomatic Playwright TypeScript code using a hybrid approach (Allocated Logic + LLM Intelligence).

## 1. Input Processing (The "Sanitizer")
Before sending code to the LLM, we must:
1.  **Strip irrelevant imports**: Remove `import org.openqa.selenium...` lines if they clutter the prompt, but keep them if they provide context.
2.  **Identify TestNG Annotations**: Regex-scan for `@Test`, `@BeforeClass`, etc., to hint the LLM.
3.  **Escape Characters**: JSON-escape the source code string.

## 2. Prompt Engineering Strategy
We use `codellama` (Ollama) with a **Few-Shot Chain-of-Thought** prompt.

### The System Prompt
```text
You are an expert Test Automation Architect.
Your task is to convert Selenium Java (TestNG) code to Playwright TypeScript.

Rules:
1.  **Strict Typing**: Use TypeScript interfaces where possible.
2.  **Async/Await**: Playwright is async. All interactions must be awaited.
3.  **Locators**: Convert `By.id("foo")` to `page.locator("#foo")`.
4.  **Test Runner**: Convert `@Test` to `test('name', async ({ page }) => { ... })`.
5.  **Page Object Model**: If the input looks like a Page Object, output a Class with `constructor(page: Page)`.
6.  **No Hallucinations**: If you don't know a library, leave a TODO comment.

Input Code:
{source_code}

Output (TypeScript Only):
```

## 3. Output Validation (The "Guard")
After receiving the LLM response:
1.  **Extract Code**: Use Regex to pull code from markdown code blocks (```typescript ... ```).
2.  **Basic Syntax Check**: Ensure `import { test, expect } from '@playwright/test';` is present.
3.  **Fallback**: If the LLM returns empty/garbage, return a "Conversion Failed" error with the raw response.

## 4. Error Handling
- **LLM Timeout**: If Ollama takes > 60s, return "Timeout".
- **LLM Error**: If 500/404, return "Ollama Connection Error".

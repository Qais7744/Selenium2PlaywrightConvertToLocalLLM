"""
Smart LLM-Powered Selenium to Playwright Converter

Uses Ollama LLM with expert prompting for accurate conversion.
Falls back to pattern matching only if LLM fails.
"""

import re
import json
import requests
from typing import Dict, Any


def create_conversion_prompt(java_code: str, language: str) -> str:
    """Create expert prompt for LLM conversion with language-specific instructions."""
    
    # Language-specific configuration
    if language == "typescript":
        lang_name = "TypeScript"
        import_syntax = "import { test, expect } from '@playwright/test';"
        use_types = "You may use TypeScript type annotations (e.g., `const title: string = ...`) where appropriate."
        file_ext = ".spec.ts"
        module_system = "ES6 modules (import/export)"
    else:  # javascript
        lang_name = "JavaScript"
        import_syntax = "const { test, expect } = require('@playwright/test');"
        use_types = "DO NOT use TypeScript type annotations. Use plain JavaScript."
        file_ext = ".spec.js"
        module_system = "CommonJS (require/module.exports)"
    
    # Build prompt with proper escaping
    prompt_parts = [
        f"You are an expert Test Automation Engineer specializing in converting Selenium Java code to Playwright {lang_name}.",
        "",
        f"## TARGET LANGUAGE: {lang_name}",
        f"File extension: {file_ext}",
        f"Module system: {module_system}",
        "",
        "## CRITICAL RULES - FOLLOW STRICTLY:",
        "",
        "### 1. IMPORTS (MUST USE THIS EXACT SYNTAX)",
        f"For {lang_name}, use:",
        "```",
        import_syntax,
        "```",
        "- NEVER use: `import { chromium } from 'playwright'` or browser launching",
        "- NEVER mix import styles",
        "",
        "### 2. LANGUAGE SPECIFIC RULES",
        use_types,
        f"- Use {module_system} consistently throughout the file",
        f"- Ensure syntax is valid {lang_name}",
        "",
        "### 3. TEST STRUCTURE",
        "- Wrap all tests in: `test.describe('Suite Name', () => { ... })`",
        "- Convert methods to: `test('method name', async ({ page }) => { ... })`",
        "- Convert @BeforeClass to: `test.beforeAll(async ({ page }) => { ... })`",
        "- Convert @AfterClass to: `test.afterAll(async ({ page }) => { ... })`",
        "",
        "### 4. BROWSER HANDLING",
        "- NEVER manually launch browser (no `chromium.launch()`)",
        "- NEVER create `browser.newPage()`",
        "- ALWAYS use the `{ page }` fixture provided by Playwright Test",
        "",
        "### 5. SELENIUM TO PLAYWRIGHT MAPPING",
        "| Selenium Java | Playwright |",
        "|--------------|-------------------|",
        "| `driver.get(url)` | `await page.goto(url)` |",
        "| `driver.findElement(By.id(\"x\"))` | `page.locator(\"#x\")` |",
        "| `driver.findElement(By.cssSelector(\"x\"))` | `page.locator(\"x\")` |",
        "| `driver.findElement(By.className(\"x\"))` | `page.locator(\".x\")` |",
        "| `driver.findElement(By.xpath(\"x\"))` | `page.locator(\"xpath=x\")` |",
        "| `element.sendKeys(\"text\")` | `await element.fill(\"text\")` |",
        "| `element.click()` | `await element.click()` |",
        "| `element.getText()` | `await element.innerText()` |",
        "| `driver.getTitle()` | `await page.title()` |",
        "| `driver.getCurrentUrl()` | `await page.url()` |",
        "| `Thread.sleep(ms)` | `await page.waitForTimeout(ms)` |",
        "| `System.out.println(x)` | `console.log(x)` |",
        "| `Assert.assertEquals(a,b)` | `expect(a).toBe(b)` |",
        "| `Assert.assertTrue(x)` | `expect(x).toBeTruthy()` |",
        "",
        "### 6. REMOVE ALL JAVA CODE",
        "- Remove: `System.setProperty`, `WebDriver`, `ChromeDriver`",
        "- Remove: `public`, `private`, `static`, `void` keywords",
        "- Remove: `By.id`, `By.cssSelector` - use string selectors directly",
        "",
        "### 7. ERROR HANDLING",
        "- Convert `catch (Exception e)` to `catch (e)`",
        "- Convert `e.printStackTrace()` to `console.error(e)`",
        "",
        f"## EXAMPLE CONVERSION FOR {lang_name}:",
        "",
        "**Input Java:**",
        "```java",
        "@Test",
        "public void loginTest() {",
        '    driver.get("https://example.com");',
        '    driver.findElement(By.id("user")).sendKeys("admin");',
        '    Assert.assertEquals(driver.getTitle(), "Home");',
        "}",
        "```",
        "",
        f"**Output Playwright {lang_name}:**",
        f"```{language}",
        import_syntax,
        "",
        "test.describe('TestSuite', () => {",
        "    test('loginTest', async ({ page }) => {",
        '        await page.goto("https://example.com")',
        '        await page.locator("#user").fill("admin")',
        '        expect(await page.title()).toBe("Home")',
        "    });",
        "});",
        "```",
        "",
        f"## NOW CONVERT THIS CODE TO {lang_name}:",
        "",
        "```java",
        java_code,
        "```",
        "",
        f"## OUTPUT (Playwright {lang_name} ONLY - no explanations):",
    ]
    
    return "\n".join(prompt_parts)


def call_llm(prompt: str, model: str = "qwen2.5-coder:0.5b", timeout: int = 300) -> str:
    """Call Ollama LLM for conversion."""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low for consistent output
                    "num_predict": 2000,  # Shorter for faster response
                }
            },
            timeout=timeout  # 5 minutes max
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except Exception as e:
        raise Exception(f"LLM call failed: {str(e)}")


def extract_code_block(text: str) -> str:
    """Extract code from LLM response."""
    # Try to find code block
    # Pattern for TypeScript/JavaScript code blocks
    match = re.search(r'```(?:typescript|javascript|ts|js)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Generic code block
    match = re.search(r'```\s*\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # If no code block, return as-is (might be plain code)
    return text.strip()


def validate_and_fix(code: str, language: str) -> str:
    """Validate output and fix common issues based on target language."""
    
    # Language-specific import check and fix
    if language == "typescript":
        # TypeScript: ES6 import
        if 'from \'@playwright/test\'' not in code and 'from "@playwright/test"' not in code:
            code = "import { test, expect } from '@playwright/test';\n\n" + code
        # Remove CommonJS require if present
        code = re.sub(r"const\s*\{\s*test\s*,\s*expect\s*\}\s*=\s*require\s*\(\s*['\"]@playwright/test['\"]\s*\)\s*;?\n?", '', code)
    else:
        # JavaScript: CommonJS require
        if 'require(\'@playwright/test\')' not in code and 'require("@playwright/test")' not in code:
            code = "const { test, expect } = require('@playwright/test');\n\n" + code
        # Remove ES6 import if present
        code = re.sub(r"import\s*\{\s*test\s*,\s*expect\s*\}\s*from\s*['\"]@playwright/test['\"]\s*;?\n?", '', code)
    
    # Remove chromium imports if present (applies to both)
    code = re.sub(r"import\s*\{\s*chromium\s*\}\s*from\s*['\"]playwright['\"];?\n?", '', code)
    
    # Remove manual browser launching (applies to both)
    code = re.sub(r'const\s+\w+\s*=\s*await\s+chromium\.launch[^;]*;?', '', code)
    code = re.sub(r'const\s+\w+\s*=\s*await\s+browser\.newPage[^;]*;?', '', code)
    code = re.sub(r'await\s+browser\.close\s*\(\s*\);?', '', code)
    
    # Ensure test wrapper exists
    if 'test.describe' not in code and "test('" in code:
        # Wrap individual tests in describe
        code = re.sub(r"(test\s*\(\s*['\"])", r"test.describe('Converted Tests', () => {\n    \1", code)
        code += "\n});"
    
    # Fix common LLM mistakes
    code = re.sub(r'By\.id\s*\(\s*"([^"]+)"\s*\)', r'"#\1"', code)
    code = re.sub(r'By\.cssSelector\s*\(\s*"([^"]+)"\s*\)', r'"\1"', code)
    code = re.sub(r'By\.className\s*\(\s*"([^"]+)"\s*\)', r'".\1"', code)
    
    # Remove Java keywords
    code = re.sub(r'\bpublic\s+', '', code)
    code = re.sub(r'\bprivate\s+', '', code)
    code = re.sub(r'\bstatic\s+', '', code)
    code = re.sub(r'\bvoid\s+', '', code)
    
    return code


def convert_with_llm(java_code: str, language: str = "typescript") -> Dict[str, Any]:
    """Main conversion function using LLM."""
    if not java_code or not java_code.strip():
        return {"status": "error", "message": "Empty code"}
    
    # Create language-specific prompt
    prompt = create_conversion_prompt(java_code, language)
    
    try:
        # Call LLM
        llm_response = call_llm(prompt)
        
        # Extract code
        code = extract_code_block(llm_response)
        
        # Validate and fix with language context
        code = validate_and_fix(code, language)
        
        # Final validation
        errors = []
        forbidden = ['chromium.launch', 'browser.launch', 'System.setProperty', 
                     'WebDriver ', 'ChromeDriver', 'public static void main']
        for pattern in forbidden:
            if pattern in code:
                errors.append(f"Contains: {pattern}")
        
        if errors:
            return {
                "status": "warning",
                "converted_code": code,
                "errors": errors
            }
        
        return {
            "status": "success",
            "converted_code": code,
            "language": language
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# Simple test
if __name__ == "__main__":
    test = '''import org.openqa.selenium.*;
import org.testng.annotations.*;

public class Test {
    @Test
    public void login() {
        driver.get("https://example.com");
        driver.findElement(By.id("user")).sendKeys("admin");
        Assert.assertEquals(driver.getTitle(), "Home");
    }
}'''
    
    print("="*60)
    print("TESTING TYPESCRIPT CONVERSION:")
    print("="*60)
    result_ts = convert_with_llm(test, "typescript")
    print(result_ts.get('converted_code', 'Error'))
    
    print("\n" + "="*60)
    print("TESTING JAVASCRIPT CONVERSION:")
    print("="*60)
    result_js = convert_with_llm(test, "javascript")
    print(result_js.get('converted_code', 'Error'))

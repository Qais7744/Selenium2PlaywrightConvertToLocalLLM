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
    """Create expert prompt for LLM conversion."""
    lang = "TypeScript" if language == "typescript" else "JavaScript"
    
    return f"""You are an expert Test Automation Engineer specializing in converting Selenium Java code to Playwright {lang}.

## CONVERSION RULES - FOLLOW STRICTLY:

### 1. IMPORTS
- ALWAYS use: `import {{ test, expect }} from '@playwright/test'`
- NEVER use: `import {{ chromium }} from 'playwright'` or browser launching

### 2. TEST STRUCTURE
- Wrap all tests in: `test.describe('Suite Name', () => {{ ... }})`
- Convert methods to: `test('method name', async ({{ page }}) => {{ ... }})`
- Convert @BeforeClass to: `test.beforeAll(async ({{ page }}) => {{ ... }})`
- Convert @AfterClass to: `test.afterAll(async ({{ page }}) => {{ ... }})`

### 3. BROWSER HANDLING
- NEVER manually launch browser (no `chromium.launch()`)
- NEVER create `browser.newPage()`
- ALWAYS use the `{{ page }}` fixture provided by Playwright Test

### 4. SELENIUM TO PLAYWRIGHT MAPPING
| Selenium Java | Playwright {lang} |
|--------------|-------------------|
| `driver.get(url)` | `await page.goto(url)` |
| `driver.findElement(By.id("x"))` | `page.locator("#x")` |
| `driver.findElement(By.cssSelector("x"))` | `page.locator("x")` |
| `driver.findElement(By.className("x"))` | `page.locator(".x")` |
| `driver.findElement(By.xpath("x"))` | `page.locator("xpath=x")` |
| `element.sendKeys("text")` | `await element.fill("text")` |
| `element.click()` | `await element.click()` |
| `element.getText()` | `await element.innerText()` |
| `driver.getTitle()` | `await page.title()` |
| `driver.getCurrentUrl()` | `await page.url()` |
| `Thread.sleep(ms)` | `await page.waitForTimeout(ms)` |
| `System.out.println(x)` | `console.log(x)` |
| `Assert.assertEquals(a,b)` | `expect(a).toBe(b)` |
| `Assert.assertTrue(x)` | `expect(x).toBeTruthy()` |

### 5. REMOVE ALL JAVA CODE
- Remove: `System.setProperty`, `WebDriver`, `ChromeDriver`
- Remove: `public`, `private`, `static`, `void` keywords
- Remove: `By.id`, `By.cssSelector` - use string selectors directly
- Remove: semicolons at end of lines (TypeScript style)

### 6. ERROR HANDLING
- Convert `catch (Exception e)` to `catch (e)`
- Convert `e.printStackTrace()` to `console.error(e)`

## EXAMPLE CONVERSION:

**Input Java:**
```java
@Test
public void loginTest() {{
    driver.get("https://example.com");
    driver.findElement(By.id("user")).sendKeys("admin");
    Assert.assertEquals(driver.getTitle(), "Home");
}}
```

**Output Playwright {lang}:**
```typescript
import {{ test, expect }} from '@playwright/test';

test.describe('TestSuite', () => {{
    test('loginTest', async ({{ page }}) => {{
        await page.goto("https://example.com")
        await page.locator("#user").fill("admin")
        expect(await page.title()).toBe("Home")
    }});
}});
```

## NOW CONVERT THIS CODE:

```java
{java_code}
```

## OUTPUT (Playwright {lang} ONLY - no explanations):
"""


def call_llm(prompt: str, model: str = "qwen2.5-coder:0.5b", timeout: int = 120) -> str:
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
                    "num_predict": 4000,  # Allow long responses
                }
            },
            timeout=timeout
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except Exception as e:
        raise Exception(f"LLM call failed: {str(e)}")


def extract_code_block(text: str) -> str:
    """Extract code from LLM response."""
    # Try to find code block
    patterns = [
        r'```(?:typescript|javascript|ts|js)?\s*\n?(.*?)\n?```',
        r'```\s*\n?(.*?)\n?```',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
    
    # If no code block, return as-is (might be plain code)
    return text.strip()


def validate_and_fix(code: str) -> str:
    """Validate output and fix common issues."""
    
    # Must have Playwright import
    if 'from \'@playwright/test\'' not in code and 'from "@playwright/test"' not in code:
        code = "import { test, expect } from '@playwright/test';\n\n" + code
    
    # Remove chromium imports if present
    code = re.sub(r"import\s*\{\s*chromium\s*\}\s*from\s*['\"]playwright['\"];?\n?", '', code)
    
    # Remove manual browser launching
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
    
    # Create prompt
    prompt = create_conversion_prompt(java_code, language)
    
    try:
        # Call LLM
        llm_response = call_llm(prompt)
        
        # Extract code
        code = extract_code_block(llm_response)
        
        # Validate and fix
        code = validate_and_fix(code)
        
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
            "converted_code": code
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
    
    print("Converting...")
    result = convert_with_llm(test, "typescript")
    
    if result['status'] == 'success':
        print("\n✅ SUCCESS:")
        print(result['converted_code'])
    else:
        print(f"\n❌ {result['status'].upper()}:")
        if 'converted_code' in result:
            print(result['converted_code'])
        if 'errors' in result:
            for e in result['errors']:
                print(f"  - {e}")
        if 'message' in result:
            print(f"  Message: {result['message']}")

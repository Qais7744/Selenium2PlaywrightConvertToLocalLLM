"""
Fixed Code Converter for Selenium2Playwright

Creates proper 1:1 behavior-equivalent conversions.
Does NOT add extra actions or hallucinate code.
"""

import re
import json
import time
import asyncio
import hashlib
from typing import Optional, Dict, Any
from dataclasses import dataclass

import aiohttp


# =============================================================================
# Pattern-Based Conversion (No Hallucination)
# =============================================================================

def convert_selenium_to_playwright(java_code: str, language: str = "typescript") -> Optional[str]:
    """
    Convert Selenium Java to Playwright with proper 1:1 behavior equivalence.
    Does NOT add extra actions not present in original code.
    """
    try:
        code = java_code.strip()
        
        # Detect code type
        has_test_annotation = '@Test' in code
        has_main_method = 'public static void main' in code
        is_page_object = 'class' in code and ('WebElement' in code or 'By.' in code)
        
        # Remove Java imports and package
        code = re.sub(r'package\s+[\w.]+;', '', code)
        code = re.sub(r'import\s+[^;]+;', '', code)
        
        # Convert based on code type
        if has_test_annotation:
            return convert_test_method(code, language)
        elif has_main_method:
            return convert_main_method(code, language)
        elif is_page_object:
            return convert_page_object(code, language)
        else:
            # Generic conversion
            return convert_generic(code, language)
            
    except Exception as e:
        print(f"Conversion error: {e}")
        return None


def convert_test_method(code: str, language: str) -> str:
    """Convert @Test method to Playwright test."""
    
    # Convert @Test annotation and method signature
    code = re.sub(
        r'@Test(?:\([^)]*\))?\s*\n\s*public\s+void\s+(\w+)\s*\(\s*\)\s*\{',
        r"test('\1', async ({ page }) => {",
        code
    )
    
    # Remove WebDriver setup
    code = re.sub(r'\s*WebDriver\s+\w+\s*=\s*new\s+\w+Driver\([^)]*\)\s*;\s*\n?', '\n', code)
    code = re.sub(r'\s*driver\.quit\(\)\s*;\s*\n?', '\n', code)
    
    # Convert navigation
    code = re.sub(
        r'driver\.get\s*\(\s*"([^"]+)"\s*\)',
        r'await page.goto("\1")',
        code
    )
    
    # Convert findElement patterns
    code = re.sub(
        r'driver\.findElement\s*\(\s*By\.id\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator("#\1")',
        code
    )
    code = re.sub(
        r'driver\.findElement\s*\(\s*By\.cssSelector\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator("\1")',
        code
    )
    code = re.sub(
        r'driver\.findElement\s*\(\s*By\.xpath\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator("xpath=\1")',
        code
    )
    code = re.sub(
        r'driver\.findElement\s*\(\s*By\.className\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator(".\1")',
        code
    )
    code = re.sub(
        r'driver\.findElement\s*\(\s*By\.name\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator("[name=\1]")',
        code
    )
    
    # Convert actions on elements
    code = re.sub(
        r'\.sendKeys\s*\(\s*"([^"]*)"\s*\)',
        r'.fill("\1")',
        code
    )
    code = re.sub(r'\.click\s*\(\s*\)', '.click()', code)
    code = re.sub(r'\.clear\s*\(\s*\)', '.clear()', code)
    code = re.sub(r'\.getText\s*\(\s*\)', '.innerText()', code)
    code = re.sub(r'\.isDisplayed\s*\(\s*\)', '.isVisible()', code)
    code = re.sub(r'\.isEnabled\s*\(\s*\)', '.isEnabled()', code)
    
    # Convert title
    code = re.sub(
        r'driver\.getTitle\s*\(\s*\)',
        r'await page.title()',
        code
    )
    
    # Convert current URL
    code = re.sub(
        r'driver\.getCurrentUrl\s*\(\s*\)',
        r'await page.url()',
        code
    )
    
    # Convert System.out.println to console.log
    code = re.sub(
        r'System\.out\.println\s*\(\s*([^)]+)\s*\)',
        r'console.log(\1)',
        code
    )
    
    # Convert Thread.sleep
    code = re.sub(
        r'Thread\.sleep\s*\(\s*(\d+)\s*\)',
        r'await page.waitForTimeout(\1)',
        code
    )
    
    # Convert assertions
    code = re.sub(
        r'Assert\.assertEquals\s*\(\s*"([^"]+)"\s*,\s*([^)]+)\)',
        r'expect(\2).toBe("\1")',
        code
    )
    code = re.sub(
        r'Assert\.assertTrue\s*\(\s*([^)]+)\)',
        r'expect(\1).toBeTruthy()',
        code
    )
    code = re.sub(
        r'Assert\.assertFalse\s*\(\s*([^)]+)\)',
        r'expect(\1).toBeFalsy()',
        code
    )
    code = re.sub(
        r'Assert\.assertNull\s*\(\s*([^)]+)\)',
        r'expect(\1).toBeNull()',
        code
    )
    code = re.sub(
        r'Assert\.assertNotNull\s*\(\s*([^)]+)\)',
        r'expect(\1).not.toBeNull()',
        code
    )
    
    # Add await to async operations
    code = re.sub(r'^(\s+)(page\.locator)', r'\1await \2', code, flags=re.MULTILINE)
    code = re.sub(r'^(\s+)(page\.goto)', r'\1await \2', code, flags=re.MULTILINE)
    code = re.sub(r'^(\s+)(page\.title)', r'\1await \2', code, flags=re.MULTILINE)
    code = re.sub(r'^(\s+)(page\.url)', r'\1await \2', code, flags=re.MULTILINE)
    
    # Clean up Java syntax
    code = re.sub(r'\bString\s+(\w+)', r'const \1', code)
    code = re.sub(r'\bWebElement\s+(\w+)', r'const \1', code)
    code = re.sub(r'\bpublic\s+', '', code)
    code = re.sub(r'\bprivate\s+', '', code)
    
    # Fix indentation
    lines = code.split('\n')
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            new_lines.append(line)
        elif new_lines and new_lines[-1].strip():
            new_lines.append(line)
    code = '\n'.join(new_lines)
    
    # Clean up remaining closing braces
    code = code.rstrip()
    
    # Remove extra closing braces from class
    brace_count = code.count('{') - code.count('}')
    while brace_count < 0:
        code = code.rstrip()
        if code.endswith('}'):
            code = code[:-1].rstrip()
        brace_count += 1
    
    # Ensure proper test closing
    if not code.endswith('});'):
        code = code.rstrip() + '\n});'
    
    # Fix indentation
    lines = code.split('\n')
    fixed_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            # Don't add extra indentation to the test() line
            if stripped.startswith("test('"):
                fixed_lines.append(stripped)
            else:
                fixed_lines.append('    ' + stripped)
        else:
            fixed_lines.append('')
    code = '\n'.join(fixed_lines)
    
    # Add imports
    is_ts = language.lower() == "typescript"
    if is_ts:
        imports = "import { test, expect } from '@playwright/test';\n\n"
    else:
        imports = "const { test, expect } = require('@playwright/test');\n\n"
    
    return imports + code


def convert_main_method(code: str, language: str) -> str:
    """Convert main() method to Playwright test."""
    
    # Extract class name first
    class_match = re.search(r'public\s+class\s+(\w+)', code)
    class_name = class_match.group(1) if class_match else 'Test'
    
    # Remove class declaration and braces
    code = re.sub(r'public\s+class\s+\w+\s*\{', '', code)
    code = re.sub(r'\}\s*$', '', code)  # Remove final class brace
    
    # Convert main method signature
    code = re.sub(
        r'public\s+static\s+void\s+main\s*\(\s*String\s*\[\s*\]\s*\w*\s*\)\s*\{',
        r"test('" + class_name + "', async ({ page }) => {",
        code
    )
    
    # Remove closing brace of main method (will be replaced with });)
    code = re.sub(r'\}\s*$', '', code)
    
    # Apply common conversions
    code = apply_common_conversions(code, language)
    
    # Ensure proper closing
    code = code.rstrip()
    if not code.endswith('});'):
        code = code + '\n});'
    
    # Fix indentation
    lines = code.split('\n')
    fixed_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            if stripped.startswith("test('"):
                fixed_lines.append(stripped)
            else:
                fixed_lines.append('    ' + stripped)
        else:
            fixed_lines.append('')
    code = '\n'.join(fixed_lines)
    
    # Add imports
    is_ts = language.lower() == "typescript"
    if is_ts:
        imports = "import { test, expect } from '@playwright/test';\n\n"
    else:
        imports = "const { test, expect } = require('@playwright/test');\n\n"
    
    return imports + code


def convert_page_object(code: str, language: str) -> str:
    """Convert Page Object class to Playwright Page Object."""
    
    # Convert class declaration
    code = re.sub(
        r'public\s+class\s+(\w+)',
        r'export class \1',
        code
    )
    
    # Convert WebDriver constructor parameter to Page
    code = re.sub(
        r'private\s+WebDriver\s+(\w+)',
        r'private page: Page',
        code
    )
    
    # Convert constructor
    if language.lower() == "typescript":
        code = re.sub(
            r'public\s+(\w+)\s*\(\s*WebDriver\s+\w+\s*\)',
            r'constructor(private page: Page)',
            code
        )
    else:
        code = re.sub(
            r'public\s+(\w+)\s*\(\s*WebDriver\s+\w+\s*\)',
            r'constructor(page) { this.page = page; }',
            code
        )
    
    # Apply common conversions
    code = apply_common_conversions(code, language)
    
    # Add import for Page
    if language.lower() == "typescript":
        code = "import { Page, Locator } from '@playwright/test';\n\n" + code
    
    return code


def convert_generic(code: str, language: str) -> str:
    """Generic conversion for any Java code."""
    return apply_common_conversions(code, language)


def apply_common_conversions(code: str, language: str) -> str:
    """Apply common conversion patterns."""
    
    # Remove WebDriver setup
    code = re.sub(r'\s*WebDriver\s+\w+\s*=\s*new\s+\w+Driver\([^)]*\)\s*;\s*\n?', '\n', code)
    code = re.sub(r'\s*driver\.quit\(\)\s*;\s*\n?', '\n', code)
    
    # Convert navigation
    code = re.sub(
        r'driver\.get\s*\(\s*"([^"]+)"\s*\)',
        r'await page.goto("\1")',
        code
    )
    
    # Convert findElement patterns
    code = re.sub(
        r'driver\.findElement\s*\(\s*By\.id\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator("#\1")',
        code
    )
    code = re.sub(
        r'driver\.findElement\s*\(\s*By\.cssSelector\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator("\1")',
        code
    )
    code = re.sub(
        r'driver\.findElement\s*\(\s*By\.xpath\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator("xpath=\1")',
        code
    )
    code = re.sub(
        r'driver\.findElement\s*\(\s*By\.className\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator(".\1")',
        code
    )
    code = re.sub(
        r'driver\.findElement\s*\(\s*By\.name\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator("[name=\1]")',
        code
    )
    
    # Convert actions
    code = re.sub(r'\.sendKeys\s*\(\s*"([^"]*)"\s*\)', r'.fill("\1")', code)
    code = re.sub(r'\.click\s*\(\s*\)', '.click()', code)
    code = re.sub(r'\.clear\s*\(\s*\)', '.clear()', code)
    code = re.sub(r'\.getText\s*\(\s*\)', '.innerText()', code)
    code = re.sub(r'\.isDisplayed\s*\(\s*\)', '.isVisible()', code)
    code = re.sub(r'\.isEnabled\s*\(\s*\)', '.isEnabled()', code)
    
    # Convert title and URL
    code = re.sub(r'driver\.getTitle\s*\(\s*\)', r'await page.title()', code)
    code = re.sub(r'driver\.getCurrentUrl\s*\(\s*\)', r'await page.url()', code)
    
    # Convert System.out.println
    code = re.sub(r'System\.out\.println\s*\(\s*([^)]+)\s*\)', r'console.log(\1)', code)
    
    # Convert Thread.sleep
    code = re.sub(r'Thread\.sleep\s*\(\s*(\d+)\s*\)', r'await page.waitForTimeout(\1)', code)
    
    # Convert waits
    code = re.sub(
        r'WebDriverWait.*?presenceOfElementLocated.*?By\.(\w+)\s*\(\s*"([^"]+)"\s*\)',
        r'await page.waitForSelector(/* \1=\2 */)',
        code
    )
    
    # Add await
    code = re.sub(r'^(\s+)(page\.locator)', r'\1await \2', code, flags=re.MULTILINE)
    code = re.sub(r'^(\s+)(page\.goto)', r'\1await \2', code, flags=re.MULTILINE)
    
    # Clean up Java syntax
    code = re.sub(r'\bString\s+(\w+)', r'const \1', code)
    code = re.sub(r'\bWebElement\s+(\w+)', r'const \1', code)
    code = re.sub(r'\bpublic\s+', '', code)
    code = re.sub(r'\bprivate\s+', '', code)
    
    # Clean up extra braces at end
    code = re.sub(r'\n{3,}', '\n\n', code)
    
    return code.strip()


# =============================================================================
# Ollama Client for Complex Cases
# =============================================================================

class OllamaClient:
    """Ollama client for complex conversions."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5-coder:0.5b"):
        self.base_url = base_url
        self.model = model
        self.generate_url = f"{base_url}/api/generate"
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            timeout = aiohttp.ClientTimeout(total=60, connect=5)
            self._session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self._session
    
    async def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate code from prompt."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": max_tokens,
            }
        }
        
        session = await self._get_session()
        
        async with session.post(self.generate_url, json=payload) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("response", "")
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()


# =============================================================================
# Main Converter Class
# =============================================================================

class CodeConverter:
    """Main converter with pattern matching + LLM fallback."""
    
    def __init__(self, model: str = "qwen2.5-coder:0.5b"):
        self.client = OllamaClient(model=model)
        self._cache: Dict[str, str] = {}
    
    def _get_cache_key(self, code: str, lang: str) -> str:
        return hashlib.md5(f"{code}:{lang}".encode()).hexdigest()
    
    def _build_llm_prompt(self, code: str, lang: str) -> str:
        lang_name = "TypeScript" if lang == "typescript" else "JavaScript"
        
        return f"""Convert this Selenium Java code to Playwright {lang_name}.

IMPORTANT RULES:
1. Convert ONLY the existing code - do NOT add new actions
2. Maintain exact behavior - if Java code doesn't click, don't add click
3. Use proper Playwright syntax:
   - driver.get() -> await page.goto()
   - driver.findElement(By.id()) -> page.locator("#id")
   - .sendKeys() -> .fill()
   - driver.getTitle() -> await page.title()
   - System.out.println() -> console.log()
4. Add test() wrapper if it's a test method
5. Return ONLY valid code, no explanations

Java code:
```java
{code}
```

Playwright {lang_name} code:"""
    
    def _extract_code(self, raw: str) -> str:
        """Extract code from LLM response."""
        # Try code blocks
        patterns = [
            r'```(?:typescript|javascript|ts|js)?\s*\n?(.*?)\n?```',
            r'```\s*\n?(.*?)\n?```',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, raw, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return raw.strip()
    
    async def convert(self, java_code: str, language: str = "typescript") -> Dict[str, Any]:
        """Convert Java code to Playwright."""
        start = time.time()
        
        java_code = java_code.strip()
        if not java_code:
            return {"status": "error", "message": "Empty code", "time": 0}
        
        # Check cache
        cache_key = self._get_cache_key(java_code, language)
        if cache_key in self._cache:
            return {
                "status": "success",
                "converted_code": self._cache[cache_key],
                "method": "cache",
                "time": round(time.time() - start, 3)
            }
        
        # Try pattern-based conversion
        pattern_result = convert_selenium_to_playwright(java_code, language)
        if pattern_result:
            self._cache[cache_key] = pattern_result
            return {
                "status": "success",
                "converted_code": pattern_result,
                "method": "pattern",
                "time": round(time.time() - start, 3)
            }
        
        # Fallback to LLM for complex cases
        prompt = self._build_llm_prompt(java_code, language)
        
        try:
            raw = await self.client.generate(prompt, max_tokens=2048)
            result = self._extract_code(raw)
            
            # Add imports if missing
            if 'import' not in result and 'require' not in result:
                if language == "typescript":
                    result = "import { test, expect } from '@playwright/test';\n\n" + result
                else:
                    result = "const { test, expect } = require('@playwright/test');\n\n" + result
            
            self._cache[cache_key] = result
            
            return {
                "status": "success",
                "converted_code": result,
                "method": "llm",
                "time": round(time.time() - start, 3)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "time": round(time.time() - start, 3)
            }
    
    async def close(self):
        await self.client.close()


# =============================================================================
# Synchronous Interface
# =============================================================================

_converter: Optional[CodeConverter] = None


def get_converter() -> CodeConverter:
    global _converter
    if _converter is None:
        _converter = CodeConverter()
    return _converter


def convert_code(java_code: str, language: str = "typescript") -> str:
    """Synchronous conversion interface."""
    converter = get_converter()
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(converter.convert(java_code, language))
    
    if result['status'] == 'success':
        return result['converted_code']
    else:
        return f"// Error: {result.get('message', 'Unknown error')}"


# Test
if __name__ == "__main__":
    test = '''import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;

public class Test {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        driver.get("https://www.google.com");
        System.out.println(driver.getTitle());
        driver.quit();
    }
}'''
    
    print("INPUT:")
    print(test)
    print("\n" + "="*60)
    print("\nOUTPUT:")
    print(convert_code(test, "typescript"))

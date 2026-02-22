"""
Selenium2Playwright Converter V2 - Complete Line-by-Line Conversion

Properly converts ALL Java Selenium code to Playwright without retaining
any Java-specific syntax or functions.
"""

import re
import json
import time
import hashlib
from typing import Optional, Dict, Any

import requests


# =============================================================================
# Complete Java to Playwright Mapping
# =============================================================================

# Java code patterns to REMOVE completely (not convert)
REMOVE_PATTERNS = [
    # System properties - remove ENTIRE line including chromedriver path
    (r'System\.setProperty\s*\(\s*"[^"]+"\s*,\s*"[^"]*chromedriver[^"]*"\s*\)\s*;\s*\n?', '', re.IGNORECASE),
    (r'System\.setProperty\s*\(\s*"[^"]+"\s*,\s*"[^"]+"\s*\)\s*;\s*\n?', ''),
    (r'System\.getProperty\s*\([^)]+\)\s*;\s*\n?', ''),
    
    # WebDriver setup (Playwright handles this automatically)
    (r'WebDriver\s+\w+\s*=\s*new\s+\w+Driver\s*\([^)]*\)\s*;\s*\n?', ''),
    (r'\w+\s*=\s*new\s+\w+Driver\s*\([^)]*\)\s*;\s*\n?', ''),
    
    # driver.quit() - not needed in Playwright
    (r'\w+\.quit\s*\(\s*\)\s*;\s*\n?', ''),
    (r'\w+\.close\s*\(\s*\)\s*;\s*\n?', ''),
    
    # Package declaration
    (r'package\s+[\w.]+;\s*\n?', ''),
    
    # Most imports (will be replaced with Playwright imports)
    (r'import\s+(?!java\.time|java\.net)[^;]+;\s*\n?', ''),
    
    # Remove ANY references to chromedriver/geckodriver paths in strings
    (r'"[^"]*chromedriver[^"]*"', '""'),
    (r'"[^"]*geckodriver[^"]*"', '""'),
]

# Java to Playwright conversions
CONVERSIONS = [
    # Navigation
    (r'driver\.get\s*\(', 'await page.goto('),
    (r'\w+\.get\s*\(', 'await page.goto('),
    
    # Current URL
    (r'driver\.getCurrentUrl\s*\(\s*\)', 'await page.url()'),
    (r'\w+\.getCurrentUrl\s*\(\s*\)', 'await page.url()'),
    
    # Title
    (r'driver\.getTitle\s*\(\s*\)', 'await page.title()'),
    (r'\w+\.getTitle\s*\(\s*\)', 'await page.title()'),
    
    # Page source
    (r'driver\.getPageSource\s*\(\s*\)', 'await page.content()'),
    (r'\w+\.getPageSource\s*\(\s*\)', 'await page.content()'),
    
    # Find element - By.id
    (r'driver\.findElement\s*\(\s*By\.id\s*\(\s*"([^"]+)"\s*\)\s*\)', r'page.locator("#\1")'),
    (r'\w+\.findElement\s*\(\s*By\.id\s*\(\s*"([^"]+)"\s*\)\s*\)', r'page.locator("#\1")'),
    
    # Find element - By.cssSelector / By.css
    (r'driver\.findElement\s*\(\s*By\.cssSelector\s*\(\s*"([^"]+)"\s*\)\s*\)', r'page.locator("\1")'),
    (r'\w+\.findElement\s*\(\s*By\.cssSelector\s*\(\s*"([^"]+)"\s*\)\s*\)', r'page.locator("\1")'),
    (r'driver\.findElement\s*\(\s*By\.css\s*\(\s*"([^"]+)"\s*\)\s*\)', r'page.locator("\1")'),
    (r'\w+\.findElement\s*\(\s*By\.css\s*\(\s*"([^"]+)"\s*\)\s*\)', r'page.locator("\1")'),
    
    # Find element - By.xpath
    (r'driver\.findElement\s*\(\s*By\.xpath\s*\(\s*"([^"]+)"\s*\)\s*\)', r'page.locator("xpath=\1")'),
    (r'\w+\.findElement\s*\(\s*By\.xpath\s*\(\s*"([^"]+)"\s*\)\s*\)', r'page.locator("xpath=\1")'),
    
    # Find element - By.className
    (r'driver\.findElement\s*\(\s*By\.className\s*\(\s*"([^"]+)"\s*\)\s*\)', r'page.locator(".\1")'),
    (r'\w+\.findElement\s*\(\s*By\.className\s*\(\s*"([^"]+)"\s*\)\s*\)', r'page.locator(".\1")'),
    
    # Find element - By.name
    (r'driver\.findElement\s*\(\s*By\.name\s*\(\s*"([^"]+)"\s*\)\s*\)', r'page.locator("[name=\1]")'),
    (r'\w+\.findElement\s*\(\s*By\.name\s*\(\s*"([^"]+)"\s*\)\s*\)', r'page.locator("[name=\1]")'),
    
    # Find element - By.tagName
    (r'driver\.findElement\s*\(\s*By\.tagName\s*\(\s*"([^"]+)"\s*\)\s*\)', r'page.locator("\1")'),
    (r'\w+\.findElement\s*\(\s*By\.tagName\s*\(\s*"([^"]+)"\s*\)\s*\)', r'page.locator("\1")'),
    
    # Find element - By.linkText
    (r'driver\.findElement\s*\(\s*By\.linkText\s*\(\s*"([^"]+)"\s*\)\s*\)', r'page.locator("text=\1")'),
    (r'\w+\.findElement\s*\(\s*By\.linkText\s*\(\s*"([^"]+)"\s*\)\s*\)', r'page.locator("text=\1")'),
    
    # Find element - By.partialLinkText
    (r'driver\.findElement\s*\(\s*By\.partialLinkText\s*\(\s*"([^"]+)"\s*\)\s*\)', r'page.locator("text=/\\b\1/")'),
    (r'\w+\.findElement\s*\(\s*By\.partialLinkText\s*\(\s*"([^"]+)"\s*\)\s*\)', r'page.locator("text=/\\b\1/")'),
    
    # Find elements (plural)
    (r'driver\.findElements\s*\(\s*By\.([^)]+)\)', r'page.locator(/* \1 */).all()'),
    (r'\w+\.findElements\s*\(\s*By\.([^)]+)\)', r'page.locator(/* \1 */).all()'),
    
    # Element actions
    (r'\.sendKeys\s*\(', '.fill('),
    (r'\.click\s*\(\s*\)', '.click()'),
    (r'\.clear\s*\(\s*\)', '.clear()'),
    (r'\.submit\s*\(\s*\)', '/* .submit() not needed - click submit button instead */'),
    
    # Element info
    (r'\.getText\s*\(\s*\)', '.innerText()'),
    (r'\.getAttribute\s*\(\s*"([^"]+)"\s*\)', r'.getAttribute("\1")'),
    (r'\.isDisplayed\s*\(\s*\)', '.isVisible()'),
    (r'\.isEnabled\s*\(\s*\)', '.isEnabled()'),
    (r'\.isSelected\s*\(\s*\)', '.isChecked()'),
    
    # Select (dropdown) - using page.locator approach
    (r'new\s+Select\s*\(([^)]+)\)', r'/* Select dropdown */ \1'),
    (r'\.selectByVisibleText\s*\(', '.selectOption({ label: '),
    (r'\.selectByValue\s*\(', '.selectOption({ value: '),
    (r'\.selectByIndex\s*\(', '.selectOption({ index: '),
    
    # Waits
    (r'Thread\.sleep\s*\(\s*(\d+)\s*\)', r'await page.waitForTimeout(\1)'),
    
    # WebDriverWait - simplified
    (r'WebDriverWait\s*\w*\s*=\s*new\s+WebDriverWait\s*\([^)]+\)\s*;\s*\n?', ''),
    (r'\w+\.until\s*\(\s*ExpectedConditions\.presenceOfElementLocated\s*\(\s*By\.([^)]+)\)\s*\)', r'await page.waitForSelector(/* \1 */)'),
    (r'\w+\.until\s*\(\s*ExpectedConditions\.visibilityOfElementLocated\s*\(\s*By\.([^)]+)\)\s*\)', r'await page.waitForSelector(/* \1 */, { state: "visible" })'),
    (r'\w+\.until\s*\(\s*ExpectedConditions\.elementToBeClickable\s*\(\s*By\.([^)]+)\)\s*\)', r'await page.waitForSelector(/* \1 */)'),
    
    # Alert/Popup handling
    (r'driver\.switchTo\(\)\.alert\(\)', 'page.on("dialog", async dialog => { await dialog.accept() })'),
    (r'\w+\.switchTo\(\)\.alert\(\)', 'page.on("dialog", async dialog => { await dialog.accept() })'),
    (r'Alert\s+\w+\s*=\s*\w+\.switchTo\(\)\.alert\(\)', '/* Handle dialog with page.on("dialog") */'),
    
    # Window/Switch handling
    (r'driver\.getWindowHandles\s*\(\s*\)', 'await context.pages()'),
    (r'\w+\.getWindowHandles\s*\(\s*\)', 'await context.pages()'),
    (r'driver\.switchTo\(\)\.window\s*\(', '/* Use page = await context.newPage() */'),
    
    # Screenshot
    (r'\w+\.getScreenshotAs\s*\([^)]+\)', 'await page.screenshot({ path: "screenshot.png" })'),
    
    # Actions class
    (r'new\s+Actions\s*\(\s*\w+\s*\)', 'page'),
    (r'\.moveToElement\s*\(', '.hover('),
    (r'\.doubleClick\s*\(\s*\)', '.dblclick()'),
    (r'\.contextClick\s*\(\s*\)', '.click({ button: "right" })'),
    (r'\.dragAndDrop\s*\(', '.dragAndDrop('),
    (r'\.keyDown\s*\(', '.keyboard.down('),
    (r'\.keyUp\s*\(', '.keyboard.up('),
    (r'\.sendKeys\s*\(', '.keyboard.type('),
    (r'\.build\(\)\.perform\(\)', ''),
    
    # JavaScript execution
    (r'driver\.executeScript\s*\(', 'await page.evaluate('),
    (r'\w+\.executeScript\s*\(', 'await page.evaluate('),
    (r'driver\.executeAsyncScript\s*\(', 'await page.evaluateHandle('),
    
    # Cookies
    (r'driver\.manage\(\)\.getCookies\(\)', 'await context.cookies()'),
    (r'driver\.manage\(\)\.addCookie\s*\(', 'await context.addCookies(['),
    (r'driver\.manage\(\)\.deleteCookieNamed\s*\(', 'await context.clearCookies(/* name */)'),
    (r'driver\.manage\(\)\.deleteAllCookies\(\)', 'await context.clearCookies()'),
    
    # Logging
    (r'System\.out\.println\s*\(', 'console.log('),
    (r'System\.err\.println\s*\(', 'console.error('),
    
    # String operations - Java to JS
    (r'\.equals\s*\(', ' === '),
    (r'\.equalsIgnoreCase\s*\(', '.toLowerCase() === '),
    (r'\.contains\s*\(', '.includes('),
    (r'\.startsWith\s*\(', '.startsWith('),
    (r'\.endsWith\s*\(', '.endsWith('),
    (r'\.length\s*\(\s*\)', '.length'),
    (r'\.substring\s*\(', '.substring('),
    (r'\.indexOf\s*\(', '.indexOf('),
    (r'\.replace\s*\(', '.replace('),
    (r'\.toLowerCase\s*\(\s*\)', '.toLowerCase()'),
    (r'\.toUpperCase\s*\(\s*\)', '.toUpperCase()'),
    (r'\.trim\s*\(\s*\)', '.trim()'),
    
    # Type conversions
    (r'Integer\.parseInt\s*\(', 'parseInt('),
    (r'Double\.parseDouble\s*\(', 'parseFloat('),
    (r'String\.valueOf\s*\(', 'String('),
    
    # Assertions - TestNG/JUnit to Playwright
    (r'Assert\.assertEquals\s*\(\s*([^,]+),\s*([^)]+)\)', r'expect(\2).toBe(\1)'),
    (r'Assert\.assertTrue\s*\(\s*([^)]+)\)', r'expect(\1).toBeTruthy()'),
    (r'Assert\.assertFalse\s*\(\s*([^)]+)\)', r'expect(\1).toBeFalsy()'),
    (r'Assert\.assertNull\s*\(\s*([^)]+)\)', r'expect(\1).toBeNull()'),
    (r'Assert\.assertNotNull\s*\(\s*([^)]+)\)', r'expect(\1).not.toBeNull()'),
    (r'Assert\.fail\s*\(\s*\)', 'expect(false).toBe(true) /* FAIL */'),
    
    # Generic types to JavaScript
    (r'<String>', ''),
    (r'<Integer>', ''),
    (r'<\w+>', ''),
]


def remove_java_only_code(code: str) -> str:
    """
    Remove Java-only code that has no Playwright equivalent.
    This is more aggressive than pattern matching.
    """
    lines = code.split('\n')
    result_lines = []
    
    for line in lines:
        original = line
        stripped = line.strip()
        
        # Skip lines that are purely Java setup
        skip_patterns = [
            r'System\.setProperty\s*\(',
            r'System\.getProperty\s*\(',
            r'webdriver\.chrome\.driver',
            r'webdriver\.gecko\.driver',
            r'chromedriver',
            r'geckodriver',
            r'ChromeDriver\s*\(',
            r'FirefoxDriver\s*\(',
            r'EdgeDriver\s*\(',
            r'SafariDriver\s*\(',
            r'InternetExplorerDriver\s*\(',
            r'WebDriver\s+\w+\s*=',
            r'new\s+\w+Driver\s*\(',
        ]
        
        should_skip = False
        for pattern in skip_patterns:
            if re.search(pattern, stripped, re.IGNORECASE):
                should_skip = True
                break
        
        if not should_skip:
            result_lines.append(original)
    
    return '\n'.join(result_lines)


def convert_try_catch(code: str) -> str:
    """Convert Java try-catch-finally to JavaScript."""
    
    # Exception type to remove (keep only variable name)
    # catch (Exception e) -> catch (error)
    code = re.sub(r'catch\s*\(\s*\w+\s+(\w+)\s*\)', r'catch (\1)', code)
    
    # Common exception types
    code = re.sub(r'catch\s*\(\s*(?:Exception|Throwable|Error)\s+(\w+)\s*\)', r'catch (\1)', code)
    
    # e.printStackTrace() -> console.error(error)
    code = re.sub(r'(\w+)\.printStackTrace\s*\(\s*\)', r'console.error(\1)', code)
    
    # Remove empty finally blocks or simplify
    code = re.sub(r'finally\s*\{\s*\}', '', code)
    
    return code


def convert_java_to_playwright(java_code: str, language: str = "typescript") -> str:
    """
    Convert Java Selenium code to Playwright line-by-line.
    """
    result = java_code
    
    # Detect code type
    is_main_method = 'public static void main' in result
    has_test_annotation = '@Test' in result
    
    # Step 0: Aggressively remove Java-only code (chromedriver, WebDriver setup, etc.)
    result = remove_java_only_code(result)
    
    # Step 1: Remove Java-specific code patterns
    for pattern, replacement, *flags in REMOVE_PATTERNS:
        flag = flags[0] if flags else 0
        result = re.sub(pattern, replacement, result, flags=flag)
    
    # Step 2: Convert try-catch blocks
    result = convert_try_catch(result)
    
    # Step 3: Apply conversions (do multiple passes for nested patterns)
    for _ in range(3):  # Multiple passes to handle nested conversions
        for pattern, replacement in CONVERSIONS:
            result = re.sub(pattern, replacement, result)
    
    # Step 4: Convert method/class structure
    if is_main_method:
        result = convert_main_method_structure(result)
    elif has_test_annotation:
        result = convert_test_method_structure(result)
    else:
        # Generic class - wrap in test
        result = convert_generic_class(result)
    
    # Step 5: Clean up and format
    result = cleanup_code(result)
    
    # Step 6: Add imports
    result = add_imports(result, language)
    
    return result


def convert_main_method_structure(code: str) -> str:
    """Convert main() method structure."""
    # Extract class name
    class_match = re.search(r'public\s+class\s+(\w+)', code)
    class_name = class_match.group(1) if class_match else 'Test'
    
    # Remove class declaration
    code = re.sub(r'public\s+class\s+\w+\s*\{', '', code)
    
    # Remove main method signature
    code = re.sub(
        r'public\s+static\s+void\s+main\s*\(\s*String\s*\[\s*\]\s*\w*\s*\)\s*\{',
        "",
        code
    )
    
    # Remove class closing braces
    code = remove_extra_closing_braces(code)
    
    # Wrap in test
    code = f"test('{class_name}', async ({{ page }}) => {{\n{code}\n}});"
    
    return code


def convert_test_method_structure(code: str) -> str:
    """Convert @Test method structure."""
    # Convert @Test annotation and method signature
    code = re.sub(
        r'@Test(?:\([^)]*\))?\s*\n\s*public\s+void\s+(\w+)\s*\(\s*\)\s*\{',
        r"test('\1', async ({ page }) => {",
        code
    )
    
    # Remove any remaining class structure
    code = re.sub(r'public\s+class\s+\w+\s*\{', '', code)
    code = remove_extra_closing_braces(code)
    
    # Ensure proper closing
    if not code.rstrip().endswith('});'):
        code = code.rstrip() + '\n});'
    
    return code


def convert_generic_class(code: str) -> str:
    """Convert generic class to test."""
    # Extract class name
    class_match = re.search(r'public\s+class\s+(\w+)', code)
    class_name = class_match.group(1) if class_match else 'Test'
    
    # Remove class declaration
    code = re.sub(r'public\s+class\s+\w+\s*\{', '', code)
    
    # Remove extra braces
    code = remove_extra_closing_braces(code)
    
    # Wrap in test
    code = f"test('{class_name}', async ({{ page }}) => {{\n{code}\n}});"
    
    return code


def remove_extra_closing_braces(code: str) -> str:
    """Remove extra closing braces from class/method."""
    lines = code.split('\n')
    result_lines = []
    brace_count = 0
    
    for line in lines:
        brace_count += line.count('{') - line.count('}')
        result_lines.append(line)
    
    # Remove trailing braces that close the class
    while result_lines and result_lines[-1].strip() == '}':
        result_lines.pop()
    
    return '\n'.join(result_lines)


def cleanup_code(code: str) -> str:
    """Clean up the converted code."""
    # Fix variable declarations
    code = re.sub(r'\bString\s+(\w+)', r'const \1', code)
    code = re.sub(r'\bWebElement\s+(\w+)', r'const \1', code)
    code = re.sub(r'\bList<[^>]+>\s+(\w+)', r'const \1', code)
    code = re.sub(r'\bMap<[^>]+>\s+(\w+)', r'const \1', code)
    code = re.sub(r'\bSet<[^>]+>\s+(\w+)', r'const \1', code)
    
    # Remove access modifiers
    code = re.sub(r'\bpublic\s+', '', code)
    code = re.sub(r'\bprivate\s+', '', code)
    code = re.sub(r'\bprotected\s+', '', code)
    code = re.sub(r'\bstatic\s+', '', code)
    code = re.sub(r'\bfinal\s+', '', code)
    
    # Remove empty lines at start/end
    code = code.strip()
    
    # Fix double semicolons
    code = re.sub(r';\s*;', ';', code)
    
    # Fix spacing
    code = re.sub(r'\n{3,}', '\n\n', code)
    
    # Add await to page operations if not already there
    lines = code.split('\n')
    new_lines = []
    for line in lines:
        stripped = line.strip()
        # Add await to page operations at start of lines
        if re.match(r'^\s+page\.(locator|goto|title|url|evaluate)', stripped):
            if not stripped.startswith('await'):
                line = re.sub(r'^(\s+)(page\.)', r'\1await \2', line)
        new_lines.append(line)
    code = '\n'.join(new_lines)
    
    return code


def add_imports(code: str, language: str) -> str:
    """Add Playwright imports."""
    is_ts = language.lower() == "typescript"
    
    # Determine what imports are needed
    needs_expect = 'expect(' in code or 'toBe' in code or 'toHave' in code
    
    if needs_expect:
        if is_ts:
            imports = "import { test, expect } from '@playwright/test';\n\n"
        else:
            imports = "const { test, expect } = require('@playwright/test');\n\n"
    else:
        if is_ts:
            imports = "import { test } from '@playwright/test';\n\n"
        else:
            imports = "const { test } = require('@playwright/test');\n\n"
    
    return imports + code


# =============================================================================
# LLM Fallback (using sync requests to avoid async issues)
# =============================================================================

def llm_convert_sync(java_code: str, language: str, model: str = "qwen2.5-coder:0.5b") -> Dict[str, Any]:
    """Use LLM for complex conversions (sync version to avoid async issues)."""
    lang_name = "TypeScript" if language == "typescript" else "JavaScript"
    
    prompt = f"""Convert this Java Selenium code to Playwright {lang_name}.

CRITICAL RULES:
1. REMOVE all Java-specific code:
   - System.setProperty
   - WebDriver setup
   - public static void main
   - Exception types in catch
   - printStackTrace
   - driver.quit

2. CONVERT these patterns:
   - driver.get() -> await page.goto()
   - driver.getTitle() -> await page.title()
   - System.out.println() -> console.log()
   - Thread.sleep() -> await page.waitForTimeout()
   - try-catch -> try-catch (with JS syntax)
   - catch (Exception e) -> catch (error)
   - e.printStackTrace() -> console.error(error)

3. REMOVE empty finally blocks

4. Return ONLY valid code, no explanations.

Java code:
```java
{java_code}
```

Playwright {lang_name} code:"""
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 2048,
                }
            },
            timeout=120  # 2 minute timeout for large code
        )
        response.raise_for_status()
        data = response.json()
        raw = data.get("response", "")
        
        # Extract code
        match = re.search(r'```(?:typescript|javascript)?\s*\n?(.*?)\n?```', raw, re.DOTALL)
        if match:
            result = match.group(1).strip()
        else:
            result = raw.strip()
        
        # Add imports if missing
        if 'import' not in result and 'require' not in result:
            if language == "typescript":
                result = "import { test, expect } from '@playwright/test';\n\n" + result
            else:
                result = "const { test, expect } = require('@playwright/test');\n\n" + result
        
        return {
            "status": "success",
            "converted_code": result,
            "method": "llm"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# =============================================================================
# Main Converter Class (Sync version - no async)
# =============================================================================

class CodeConverter:
    """Main converter with pattern matching + LLM fallback."""
    
    def __init__(self, model: str = "qwen2.5-coder:0.5b"):
        self.model = model
        self._cache = {}
    
    def _get_cache_key(self, code: str, lang: str) -> str:
        return hashlib.md5(f"{code}:{lang}".encode()).hexdigest()
    
    def convert(self, java_code: str, language: str = "typescript") -> Dict[str, Any]:
        """Convert Java code to Playwright (sync version)."""
        start = time.time()
        
        if not java_code or not java_code.strip():
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
        
        # Pattern-based conversion
        try:
            result = convert_java_to_playwright(java_code, language)
            
            # Validate result
            if self._is_valid_conversion(result, java_code):
                self._cache[cache_key] = result
                return {
                    "status": "success",
                    "converted_code": result,
                    "method": "pattern",
                    "time": round(time.time() - start, 3)
                }
        except Exception as e:
            print(f"Pattern conversion failed: {e}")
        
        # Fallback to LLM for very complex cases (sync call)
        llm_result = llm_convert_sync(java_code, language, self.model)
        llm_result['time'] = round(time.time() - start, 3)
        
        if llm_result['status'] == 'success':
            self._cache[cache_key] = llm_result['converted_code']
        
        return llm_result
    
    def _is_valid_conversion(self, result: str, original: str) -> bool:
        """Check if conversion looks valid."""
        # Must have test wrapper
        if "test('" not in result and 'test("' not in result:
            return False
        
        # Should not have Java-specific code
        java_patterns = [
            'System.setProperty',
            'WebDriver ',
            'public static void main',
            'Exception e)',
            'printStackTrace',
        ]
        for pattern in java_patterns:
            if pattern in result:
                return False
        
        return True


# =============================================================================
# Synchronous Interface
# =============================================================================

_converter = None


def get_converter():
    global _converter
    if _converter is None:
        _converter = CodeConverter()
    return _converter


def convert_code(java_code: str, language: str = "typescript") -> str:
    """Synchronous conversion interface."""
    converter = get_converter()
    result = converter.convert(java_code, language)
    
    if result['status'] == 'success':
        return result['converted_code']
    else:
        return f"// Error: {result.get('message', 'Unknown error')}"


# Test
if __name__ == "__main__":
    test = '''import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;

public class SimpleSeleniumTest {
    public static void main(String[] args) {
        System.setProperty("webdriver.chrome.driver", "path/to/chromedriver");
        
        WebDriver driver = new ChromeDriver();
        
        try {
            driver.get("https://www.google.com");
            System.out.println("Page title is: " + driver.getTitle());
            Thread.sleep(3000);
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            driver.quit();
        }
    }
}'''
    
    print("="*60)
    print("INPUT:")
    print(test)
    print("\n" + "="*60)
    print("OUTPUT:")
    result = convert_code(test, "typescript")
    print(result)
    
    # Verify no Java code remains
    print("\n" + "="*60)
    print("VALIDATION:")
    java_patterns = ['System.setProperty', 'WebDriver ', 'Exception e)', 'printStackTrace', 'chromedriver']
    for pattern in java_patterns:
        if pattern in result:
            print(f"  FAIL: Found '{pattern}' in output")
        else:
            print(f"  PASS: '{pattern}' removed")

"""
Selenium2Playwright Final Converter - Complete Framework Conversion

Converts Selenium + TestNG code to proper Playwright test framework.
Handles: @BeforeClass, @Test, @AfterClass, shared state, and complex flows.
"""

import re
import json
import time
import hashlib
from typing import Optional, Dict, Any, List, Tuple
import requests


# =============================================================================
# Java to Playwright Mappings
# =============================================================================

# TestNG annotations to Playwright
ANNOTATION_MAP = {
    '@BeforeSuite': 'test.beforeAll',
    '@BeforeTest': 'test.beforeAll', 
    '@BeforeClass': 'test.beforeAll',
    '@BeforeMethod': 'test.beforeEach',
    '@Test': 'test',
    '@AfterMethod': 'test.afterEach',
    '@AfterClass': 'test.afterAll',
    '@AfterTest': 'test.afterAll',
    '@AfterSuite': 'test.afterAll',
}

# Selenium methods to Playwright
METHOD_MAP = {
    # Navigation
    'driver.get': 'await page.goto',
    'driver.navigate().to': 'await page.goto',
    'driver.navigate().back': 'await page.goBack',
    'driver.navigate().forward': 'await page.goForward',
    'driver.navigate().refresh': 'await page.reload',
    
    # Element finding - converted to direct locators
    'findElement(By.id': 'page.locator(#',
    'findElement(By.cssSelector': 'page.locator(',
    'findElement(By.css': 'page.locator(',
    'findElement(By.xpath': 'page.locator(xpath=',
    'findElement(By.className': 'page.locator(.',
    'findElement(By.name': 'page.locator([name=',
    'findElement(By.tagName': 'page.locator(',
    'findElement(By.linkText': 'page.locator(text=',
    'findElement(By.partialLinkText': 'page.locator(text=/',
    
    # Element actions
    '.sendKeys': '.fill',
    '.click()': '.click()',
    '.clear()': '.clear()',
    '.submit()': '.click() /* submit */',
    
    # Element info
    '.getText()': '.innerText()',
    '.getAttribute': '.getAttribute',
    '.isDisplayed()': '.isVisible()',
    '.isEnabled()': '.isEnabled()',
    '.isSelected()': '.isChecked()',
    
    # Page info
    'driver.getTitle()': 'await page.title()',
    'driver.getCurrentUrl()': 'await page.url()',
    'driver.getPageSource()': 'await page.content()',
}

# Java assertions to Playwright
ASSERTION_MAP = {
    'Assert.assertEquals': 'expect({1}).toBe({0})',
    'Assert.assertTrue': 'expect({0}).toBeTruthy()',
    'Assert.assertFalse': 'expect({0}).toBeFalsy()',
    'Assert.assertNull': 'expect({0}).toBeNull()',
    'Assert.assertNotNull': 'expect({0}).not.toBeNull()',
    'Assert.assertSame': 'expect({1}).toBe({0})',
    'Assert.assertNotSame': 'expect({1}).not.toBe({0})',
    'Assert.fail': 'expect(false).toBe(true) /* FAIL */',
}

# Java types to JavaScript
TYPE_MAP = {
    'String': 'const',
    'WebElement': 'const',
    'List<WebElement>': 'const',
    'int': 'const',
    'boolean': 'const',
    'double': 'const',
    'long': 'const',
    'float': 'const',
}


# =============================================================================
# Core Conversion Functions
# =============================================================================

def remove_java_boilerplate(code: str) -> str:
    """Remove Java boilerplate that doesn't convert to Playwright."""
    # Remove package
    code = re.sub(r'package\s+[\w.]+;', '', code)
    
    # Remove Selenium imports
    code = re.sub(r'import\s+org\.openqa\.selenium[^;]*;', '', code)
    code = re.sub(r'import\s+org\.testng[^;]*;', '', code)
    code = re.sub(r'import\s+java\.time[^;]*;', '', code)
    
    # Remove driver setup
    code = re.sub(r'System\.setProperty\s*\([^)]+\)\s*;', '', code)
    code = re.sub(r'WebDriver\s+\w+\s*=\s*new\s+\w+Driver\s*\([^)]*\)\s*;', '', code)
    code = re.sub(r'driver\s*=\s*new\s+\w+Driver\s*\([^)]*\)\s*;', '', code)
    
    # Remove driver teardown
    code = re.sub(r'\w+\.quit\s*\(\s*\)\s*;', '', code)
    code = re.sub(r'\w+\.close\s*\(\s*\)\s*;', '', code)
    
    # Remove access modifiers
    code = re.sub(r'\bpublic\s+', '', code)
    code = re.sub(r'\bprivate\s+', code.count('{') * ' ', code)  # Keep private vars but remove keyword
    code = re.sub(r'\bprotected\s+', '', code)
    code = re.sub(r'\bstatic\s+', '', code)
    code = re.sub(r'\bfinal\s+', '', code)
    
    return code


def convert_types(code: str) -> str:
    """Convert Java types to JavaScript."""
    for java_type, js_type in TYPE_MAP.items():
        # Match type declarations
        pattern = rf'\b{re.escape(java_type)}\s+(\w+)'
        code = re.sub(pattern, rf'{js_type} \1', code)
    return code


def convert_annotations(code: str) -> str:
    """Convert TestNG annotations to Playwright."""
    lines = code.split('\n')
    result = []
    
    for line in lines:
        stripped = line.strip()
        
        # Check for annotations with parameters
        for java_ann, pw_ann in ANNOTATION_MAP.items():
            if java_ann in stripped:
                # Extract parameters if any
                params_match = re.search(rf'{re.escape(java_ann)}\(([^)]+)\)', stripped)
                if params_match:
                    params = params_match.group(1)
                    # Handle priority, dependsOnMethods, etc.
                    if 'priority' in params or 'dependsOnMethods' in params:
                        # These don't map directly - add comment
                        result.append(f'// {stripped} - sequential execution in Playwright')
                        continue
                
                line = line.replace(java_ann, pw_ann)
                break
        
        result.append(line)
    
    return '\n'.join(result)


def convert_methods(code: str) -> str:
    """Convert Selenium methods to Playwright."""
    # Convert driver.get()
    code = re.sub(r'driver\.get\s*\(\s*"([^"]+)"\s*\)', r'await page.goto("\1")', code)
    
    # Convert findElement patterns
    # By.id
    code = re.sub(
        r'(?:driver\.)?findElement\s*\(\s*By\.id\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator("#\1")',
        code
    )
    # By.cssSelector
    code = re.sub(
        r'(?:driver\.)?findElement\s*\(\s*By\.cssSelector\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator("\1")',
        code
    )
    # By.xpath
    code = re.sub(
        r'(?:driver\.)?findElement\s*\(\s*By\.xpath\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator("xpath=\1")',
        code
    )
    # By.className
    code = re.sub(
        r'(?:driver\.)?findElement\s*\(\s*By\.className\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator(".\1")',
        code
    )
    # By.name
    code = re.sub(
        r'(?:driver\.)?findElement\s*\(\s*By\.name\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator("[name=\1]")',
        code
    )
    # By.linkText
    code = re.sub(
        r'(?:driver\.)?findElement\s*\(\s*By\.linkText\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator("text=\1")',
        code
    )
    
    # Convert element actions
    code = re.sub(r'\.sendKeys\s*\(\s*"([^"]*)"\s*\)', r'.fill("\1")', code)
    code = re.sub(r'\.click\s*\(\s*\)', '.click()', code)
    code = re.sub(r'\.clear\s*\(\s*\)', '.clear()', code)
    code = re.sub(r'\.getText\s*\(\s*\)', '.innerText()', code)
    code = re.sub(r'\.isDisplayed\s*\(\s*\)', '.isVisible()', code)
    
    # Convert driver methods
    code = re.sub(r'driver\.getTitle\s*\(\s*\)', 'await page.title()', code)
    code = re.sub(r'driver\.getCurrentUrl\s*\(\s*\)', 'await page.url()', code)
    
    # Convert Thread.sleep
    code = re.sub(r'Thread\.sleep\s*\(\s*(\d+)\s*\)', r'await page.waitForTimeout(\1)', code)
    
    # Convert System.out.println
    code = re.sub(r'System\.out\.println\s*\(', 'console.log(', code)
    
    return code


def convert_assertions(code: str) -> str:
    """Convert TestNG assertions to Playwright."""
    # Assert.assertEquals(expected, actual)
    code = re.sub(
        r'Assert\.assertEquals\s*\(\s*([^,]+),\s*([^)]+)\s*\)',
        r'expect(\2).toBe(\1)',
        code
    )
    
    # Assert.assertTrue(condition)
    code = re.sub(
        r'Assert\.assertTrue\s*\(\s*([^)]+)\s*\)',
        r'expect(\1).toBeTruthy()',
        code
    )
    
    # Assert.assertFalse(condition)
    code = re.sub(
        r'Assert\.assertFalse\s*\(\s*([^)]+)\s*\)',
        r'expect(\1).toBeFalsy()',
        code
    )
    
    # Assert.assertNull(object)
    code = re.sub(
        r'Assert\.assertNull\s*\(\s*([^)]+)\s*\)',
        r'expect(\1).toBeNull()',
        code
    )
    
    return code


def convert_exception_handling(code: str) -> str:
    """Convert Java exception handling to JavaScript."""
    # catch (Exception e) -> catch (e)
    code = re.sub(r'catch\s*\(\s*\w+\s+(\w+)\s*\)', r'catch (\1)', code)
    code = re.sub(r'catch\s*\(\s*Exception\s+(\w+)\s*\)', r'catch (\1)', code)
    
    # e.printStackTrace() -> console.error(e)
    code = re.sub(r'(\w+)\.printStackTrace\s*\(\s*\)', r'console.error(\1)', code)
    
    return code


def convert_class_structure(code: str) -> str:
    """Convert Java class structure to Playwright test structure."""
    # Extract class name
    class_match = re.search(r'class\s+(\w+)', code)
    class_name = class_match.group(1) if class_match else 'TestSuite'
    
    # Remove class declaration
    code = re.sub(r'class\s+\w+\s*\{', '', code)
    
    # Convert methods to test blocks or helper functions
    lines = code.split('\n')
    result = []
    in_method = False
    method_name = None
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Check for method start
        method_match = re.match(r'(?:void|int|String|boolean|WebElement)\s+(\w+)\s*\(\s*\)\s*\{', stripped)
        if method_match and not in_method:
            method_name = method_match.group(1)
            
            # Check if previous line was an annotation
            prev_line = lines[i-1].strip() if i > 0 else ''
            
            if 'test.beforeAll' in prev_line:
                result.append(f'test.beforeAll(async ({{ page }}) => {{')
                in_method = True
            elif 'test.beforeEach' in prev_line:
                result.append(f'test.beforeEach(async ({{ page }}) => {{')
                in_method = True
            elif 'test.afterEach' in prev_line:
                result.append(f'test.afterEach(async ({{ page }}) => {{')
                in_method = True
            elif 'test.afterAll' in prev_line:
                result.append(f'test.afterAll(async ({{ page }}) => {{')
                in_method = True
            elif 'test' in prev_line or '@Test' in prev_line:
                # It's a test method
                result.append(f"test('{method_name}', async ({{ page }}) => {{")
                in_method = True
            else:
                # It's a helper method - convert to function
                result.append(f'async function {method_name}(page) {{')
                in_method = True
            
            i += 1
            continue
        
        result.append(line)
        i += 1
    
    return '\n'.join(result)


def add_proper_closing(code: str) -> str:
    """Add proper closing braces."""
    # Count opening and closing braces
    open_count = code.count('{')
    close_count = code.count('}')
    
    # Add missing closing braces
    while close_count < open_count:
        code += '\n}'
        close_count += 1
    
    # Ensure final structure
    if not code.strip().endswith('});'):
        code = code.rstrip()
        if code.endswith('}'):
            code = code[:-1] + '});'
    
    return code


def format_code(code: str) -> str:
    """Format the converted code."""
    lines = code.split('\n')
    result = []
    indent_level = 0
    
    for line in lines:
        stripped = line.strip()
        
        # Decrease indent for closing braces
        if stripped.startswith('}'):
            indent_level = max(0, indent_level - 1)
        
        # Add proper indentation
        if stripped:
            result.append('    ' * indent_level + stripped)
        else:
            result.append('')
        
        # Increase indent for opening braces
        if stripped.endswith('{') and not stripped.startswith('//') and not stripped.startswith('*'):
            indent_level += 1
    
    return '\n'.join(result)


def add_imports(code: str, language: str) -> str:
    """Add Playwright imports."""
    needs_expect = 'expect(' in code or '.toBe' in code or '.toHave' in code
    
    if needs_expect:
        imports = "import { test, expect } from '@playwright/test';\n\n"
    else:
        imports = "import { test } from '@playwright/test';\n\n"
    
    # Wrap in test.describe for structure
    if 'test.beforeAll' in code or 'test.beforeEach' in code:
        code = f"test.describe('Test Suite', () => {{\n{code}\n}});"
    
    return imports + code


# =============================================================================
# Main Conversion Function
# =============================================================================

def convert_java_to_playwright(java_code: str, language: str = "typescript") -> str:
    """
    Complete conversion from Java Selenium + TestNG to Playwright.
    """
    result = java_code
    
    # Step 1: Remove Java boilerplate
    result = remove_java_boilerplate(result)
    
    # Step 2: Convert types
    result = convert_types(result)
    
    # Step 3: Convert annotations
    result = convert_annotations(result)
    
    # Step 4: Convert methods
    result = convert_methods(result)
    
    # Step 5: Convert assertions
    result = convert_assertions(result)
    
    # Step 6: Convert exception handling
    result = convert_exception_handling(result)
    
    # Step 7: Convert class structure
    result = convert_class_structure(result)
    
    # Step 8: Add proper closing
    result = add_proper_closing(result)
    
    # Step 9: Format
    result = format_code(result)
    
    # Step 10: Add imports
    result = add_imports(result, language)
    
    return result


# =============================================================================
# LLM Fallback for Complex Cases
# =============================================================================

def llm_convert_sync(java_code: str, language: str, model: str = "qwen2.5-coder:0.5b") -> Dict[str, Any]:
    """Use LLM for complex conversions."""
    lang_name = "TypeScript" if language == "typescript" else "JavaScript"
    
    prompt = f"""Convert this Java Selenium + TestNG code to Playwright {lang_name}.

CRITICAL CONVERSION RULES:

1. TestNG Annotations → Playwright:
   - @BeforeClass → test.beforeAll
   - @BeforeMethod → test.beforeEach
   - @Test → test
   - @AfterMethod → test.afterEach
   - @AfterClass → test.afterAll

2. Remove ALL Java boilerplate:
   - Remove: System.setProperty, WebDriver setup, driver.quit
   - Remove: package declarations, Selenium imports
   - Remove: public/private/static/final keywords

3. Convert Selenium to Playwright:
   - driver.get() → await page.goto()
   - findElement(By.id()) → page.locator("#id")
   - findElement(By.cssSelector()) → page.locator("selector")
   - .sendKeys() → .fill()
   - .click() → .click()
   - .getText() → .innerText()
   - driver.getTitle() → await page.title()
   - Thread.sleep() → await page.waitForTimeout()
   - System.out.println() → console.log()

4. Convert Assertions:
   - Assert.assertEquals(actual, expected) → expect(actual).toBe(expected)
   - Assert.assertTrue(condition) → expect(condition).toBeTruthy()
   - Assert.assertFalse(condition) → expect(condition).toBeFalsy()

5. Convert Exception Handling:
   - catch (Exception e) → catch (e)
   - e.printStackTrace() → console.error(e)

6. Structure:
   - Wrap tests in test.describe()
   - Use async ({{ page }}) for all test functions
   - Add proper imports: import {{ test, expect }} from '@playwright/test'

7. DO NOT:
   - Manually launch browser (chromium.launch)
   - Use driver variable
   - Keep Java syntax

Return ONLY the converted Playwright code.

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
                    "num_predict": 4000,  # Larger for big files
                }
            },
            timeout=180  # 3 minutes for large files
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
        
        # Ensure imports
        if 'import' not in result:
            result = "import { test, expect } from '@playwright/test';\n\n" + result
        
        return {"status": "success", "converted_code": result, "method": "llm"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


# =============================================================================
# Main Converter Class
# =============================================================================

class CodeConverter:
    """Main converter with pattern matching + LLM fallback."""
    
    def __init__(self, model: str = "qwen2.5-coder:0.5b"):
        self.model = model
        self._cache = {}
    
    def _get_cache_key(self, code: str, lang: str) -> str:
        return hashlib.md5(f"{code}:{lang}".encode()).hexdigest()
    
    def convert(self, java_code: str, language: str = "typescript") -> Dict[str, Any]:
        """Convert Java code to Playwright."""
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
            
            # Validate
            if self._is_valid_conversion(result):
                self._cache[cache_key] = result
                return {
                    "status": "success",
                    "converted_code": result,
                    "method": "pattern",
                    "time": round(time.time() - start, 3)
                }
        except Exception as e:
            print(f"Pattern conversion failed: {e}")
        
        # LLM fallback
        llm_result = llm_convert_sync(java_code, language, self.model)
        llm_result['time'] = round(time.time() - start, 3)
        
        if llm_result['status'] == 'success':
            self._cache[cache_key] = llm_result['converted_code']
        
        return llm_result
    
    def _is_valid_conversion(self, result: str) -> bool:
        """Check if conversion is valid."""
        must_have = ['test(', 'page.']
        must_not_have = [
            'System.setProperty',
            'WebDriver ',
            'public static void main',
            'driver = new',
            'chromedriver',
        ]
        
        for pattern in must_have:
            if pattern not in result:
                return False
        
        for pattern in must_not_have:
            if pattern in result:
                return False
        
        return True


# =============================================================================
# Public Interface
# =============================================================================

_converter = None


def get_converter():
    global _converter
    if _converter is None:
        _converter = CodeConverter()
    return _converter


def convert_code(java_code: str, language: str = "typescript") -> str:
    """Convert Java Selenium code to Playwright."""
    converter = get_converter()
    result = converter.convert(java_code, language)
    
    if result['status'] == 'success':
        return result['converted_code']
    else:
        return f"// Error: {result.get('message', 'Unknown error')}"


# Test
if __name__ == "__main__":
    test_code = '''import org.openqa.selenium.*;
import org.testng.Assert;
import org.testng.annotations.*;

public class SauceDemoTest {
    WebDriver driver;
    
    @BeforeClass
    public void setUp() {
        System.setProperty("webdriver.chrome.driver", "path/to/chromedriver");
        driver = new ChromeDriver();
    }
    
    @Test
    public void testLogin() {
        driver.get("https://www.saucedemo.com");
        WebElement username = driver.findElement(By.id("user-name"));
        username.sendKeys("standard_user");
        driver.findElement(By.id("password")).sendKeys("secret_sauce");
        driver.findElement(By.id("login-button")).click();
        Assert.assertEquals(driver.getTitle(), "Swag Labs");
    }
    
    @AfterClass
    public void tearDown() {
        driver.quit();
    }
}'''
    
    print("="*60)
    print("INPUT:")
    print(test_code)
    print("\n" + "="*60)
    print("OUTPUT:")
    print(convert_code(test_code, "typescript"))

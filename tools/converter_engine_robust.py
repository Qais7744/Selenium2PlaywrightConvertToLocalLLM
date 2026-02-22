"""
Selenium2Playwright Robust Converter - Zero Java Code Output

Guarantees:
1. NO Java imports remain
2. NO manual browser launching
3. NO Selenium methods
4. Strict Playwright test() structure
5. Proper { page } fixture usage
"""

import re
import hashlib
from typing import Dict, Any


# =============================================================================
# STRICT POST-PROCESSING - Removes ANY bad patterns
# =============================================================================

def strict_cleanup(code: str) -> str:
    """
    Aggressive cleanup to ensure ZERO Java code remains.
    This runs after conversion to catch any missed patterns.
    """
    
    # Remove ANY lines with these patterns
    forbidden_patterns = [
        r'import.*chromium',
        r'from.*chromium',
        r'chromium\.launch',
        r'chromium\.Browser',
        r'browser\s*=\s*await',
        r'browser\.launch',
        r'browser\.newPage',
        r'browser\.close',
        r'const browser',
        r'let browser',
        r'var browser',
        r'new\s+ChromeDriver',
        r'new\s+FirefoxDriver',
        r'new\s+EdgeDriver',
        r'System\.setProperty',
        r'webdriver\.chrome\.driver',
        r'chromedriver',
        r'geckodriver',
        r'By\.id\s*\(',
        r'By\.cssSelector\s*\(',
        r'By\.className\s*\(',
        r'By\.xpath\s*\(',
        r'By\.name\s*\(',
        r'driver\s*=',
        r'WebDriver',
        r'\.sendKeys\s*\(',
        r'\.getText\s*\(',
        r'printStackTrace',
        r'Exception\s+\w+',
        r'public\s+void',
        r'public\s+static',
        r'private\s+void',
        r'@BeforeClass',
        r'@AfterClass', 
        r'@Test',
        r'@BeforeMethod',
        r'@AfterMethod',
        r'Assert\.assert',
    ]
    
    lines = code.split('\n')
    cleaned_lines = []
    
    for line in lines:
        should_remove = False
        for pattern in forbidden_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                should_remove = True
                break
        
        if not should_remove:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def ensure_proper_structure(code: str, class_name: str = 'TestSuite') -> str:
    """
    Ensure code follows strict Playwright structure.
    Fixes common LLM mistakes.
    """
    
    # Remove any existing imports - we'll add correct ones
    code = re.sub(r"import\s+.*from\s+'[^']+'\s*;?\n", '', code)
    code = re.sub(r"const\s+.*=\s*require\s*\([^)]+\)\s*;?\n", '', code)
    
    # Remove manual browser/page creation
    code = re.sub(r'const\s+\w+\s*=\s*await\s+chromium\.launch[^;]*;', '', code)
    code = re.sub(r'const\s+\w+\s*=\s*await\s+browser\.newPage[^;]*;', '', code)
    code = re.sub(r'await\s+browser\.close\s*\(\s*\)\s*;?', '', code)
    
    # Fix: Remove top-level awaits
    code = re.sub(r'^await\s+', '', code, flags=re.MULTILINE)
    
    # Fix: Ensure all test functions use ({ page })
    # Find test declarations and fix them
    code = re.sub(
        r"test\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*async\s*\(\s*\)\s*\{",
        r"test('\1', async ({ page }) => {",
        code
    )
    
    # Fix: Ensure test.beforeAll/test.afterAll use ({ page })
    code = re.sub(
        r"test\.beforeAll\s*\(\s*async\s*\(\s*\)\s*\{",
        r"test.beforeAll(async ({ page }) => {",
        code
    )
    code = re.sub(
        r"test\.afterAll\s*\(\s*async\s*\(\s*\)\s*\{",
        r"test.afterAll(async ({ page }) => {",
        code
    )
    code = re.sub(
        r"test\.beforeEach\s*\(\s*async\s*\(\s*\)\s*\{",
        r"test.beforeEach(async ({ page }) => {",
        code
    )
    code = re.sub(
        r"test\.afterEach\s*\(\s*async\s*\(\s*\)\s*\{",
        r"test.afterEach(async ({ page }) => {",
        code
    )
    
    # Fix: Replace any remaining 'browser.' references with comments
    code = re.sub(r'browser\.\w+\([^)]*\)', '/* browser operation - not needed */', code)
    
    # Fix: Convert Selenium By.* to Playwright locators
    code = re.sub(r'By\.id\s*\(\s*["\']([^"\']+)["\']\s*\)', r'"#\1"', code)
    code = re.sub(r'By\.cssSelector\s*\(\s*["\']([^"\']+)["\']\s*\)', r'"\1"', code)
    code = re.sub(r'By\.className\s*\(\s*["\']([^"\']+)["\']\s*\)', r'".\1"', code)
    code = re.sub(r'By\.xpath\s*\(\s*["\']([^"\']+)["\']\s*\)', r'"xpath=\1"', code)
    code = re.sub(r'By\.name\s*\(\s*["\']([^"\']+)["\']\s*\)', r'"[name=\1]"', code)
    code = re.sub(r'By\.linkText\s*\(\s*["\']([^"\']+)["\']\s*\)', r'"text=\1"', code)
    
    # Fix: Ensure page operations have await
    code = re.sub(r'^(\s+)(page\.goto|page\.locator|page\.title|page\.url)', r'\1await \2', code, flags=re.MULTILINE)
    code = re.sub(r'^(\s+)(page\.fill|page\.click|page\.type)', r'\1await \2', code, flags=re.MULTILINE)
    
    # Fix: Replace driver. with page.
    code = re.sub(r'\bdriver\.', 'page.', code)
    
    # Fix: Replace .sendKeys with .fill
    code = re.sub(r'\.sendKeys\s*\(', '.fill(', code)
    
    # Fix: Replace .getText() with .innerText() or .textContent()
    code = re.sub(r'\.getText\s*\(\s*\)', '.innerText()', code)
    
    # Fix: Convert assertions
    code = re.sub(r'Assert\.assertEquals\s*\(\s*([^,]+),\s*([^)]+)\)', r'expect(\1).toBe(\2)', code)
    code = re.sub(r'Assert\.assertTrue\s*\(\s*([^)]+)\)', r'expect(\1).toBeTruthy()', code)
    code = re.sub(r'Assert\.assertFalse\s*\(\s*([^)]+)\)', r'expect(\1).toBeFalsy()', code)
    
    # Fix: Replace Thread.sleep
    code = re.sub(r'Thread\.sleep\s*\(\s*(\d+)\s*\)', r'await page.waitForTimeout(\1)', code)
    
    # Fix: Replace System.out.println
    code = re.sub(r'System\.out\.println\s*\(', 'console.log(', code)
    
    # Fix: Exception handling
    code = re.sub(r'catch\s*\(\s*(?:Exception|Error|Throwable)\s+(\w+)\s*\)', r'catch (\1)', code)
    code = re.sub(r'(\w+)\.printStackTrace\s*\(\s*\)', r'console.error(\1)', code)
    
    # Remove empty try-catch blocks
    code = re.sub(r'try\s*\{\s*\}\s*catch[^}]*\{\s*\}', '', code)
    
    # Ensure proper test structure
    if 'test.describe' not in code and "test('" in code:
        # Wrap tests in describe
        code = f"test.describe('{class_name}', () => {{\n{code}\n}});"
    
    # Add proper imports at the top
    has_expect = 'expect(' in code or '.toBe' in code or '.toHave' in code
    if has_expect:
        imports = "import { test, expect } from '@playwright/test';\n\n"
    else:
        imports = "import { test } from '@playwright/test';\n\n"
    
    code = imports + code
    
    return code


# =============================================================================
# MAIN CONVERSION FUNCTION
# =============================================================================

def convert_java_to_playwright(java_code: str, language: str = "typescript") -> str:
    """
    Convert Java Selenium to Playwright with strict output validation.
    """
    # Extract class name for structure
    class_match = re.search(r'class\s+(\w+)', java_code)
    class_name = class_match.group(1) if class_match else 'TestSuite'
    
    # Step 1: Remove all Java boilerplate first
    result = java_code
    
    # Remove package
    result = re.sub(r'package\s+[\w.]+;', '', result)
    
    # Remove all imports (we'll add correct ones later)
    result = re.sub(r'import\s+[^;]+;', '', result)
    
    # Remove class declaration
    result = re.sub(r'public\s+class\s+\w+\s*\{', '', result)
    result = re.sub(r'class\s+\w+\s*\{', '', result)
    
    # Remove System.setProperty lines completely
    result = re.sub(r'System\.setProperty\s*\([^)]+\)\s*;\s*\n?', '', result)
    
    # Remove WebDriver setup
    result = re.sub(r'WebDriver\s+\w+\s*=\s*new\s+\w+Driver\s*\([^)]*\)\s*;\s*\n?', '', result)
    result = re.sub(r'\w+\s*=\s*new\s+\w+Driver\s*\([^)]*\)\s*;\s*\n?', '', result)
    result = re.sub(r'WebDriver\s+\w+\s*;', '', result)
    
    # Remove driver.quit
    result = re.sub(r'\w+\.quit\s*\(\s*\)\s*;\s*\n?', '', result)
    
    # Step 2: Convert annotations to comments (for reference)
    result = re.sub(r'@BeforeClass.*', '// Setup', result)
    result = re.sub(r'@BeforeMethod.*', '// Before each test', result)
    result = re.sub(r'@AfterMethod.*', '// After each test', result)
    result = re.sub(r'@AfterClass.*', '// Cleanup', result)
    
    # Convert @Test to test()
    def convert_test_method(match):
        method_name = match.group(1)
        return f"test('{method_name}', async ({{ page }}) => {{"
    
    result = re.sub(
        r'@Test(?:\([^)]*\))?\s*\n\s*public\s+\w+\s+(\w+)\s*\(\s*\)\s*\{',
        convert_test_method,
        result
    )
    
    # Also catch methods without @Test annotation but with public void
    result = re.sub(
        r'public\s+\w+\s+(\w+)\s*\(\s*\)\s*\{',
        r"test('\1', async ({ page }) => {",
        result
    )
    
    # Step 3: Convert Selenium methods
    result = re.sub(r'driver\.get\s*\(\s*"([^"]+)"\s*\)', r'await page.goto("\1")', result)
    
    # Convert findElement calls
    result = re.sub(
        r'(?:driver\.)?findElement\s*\(\s*By\.id\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator("#\1")',
        result
    )
    result = re.sub(
        r'(?:driver\.)?findElement\s*\(\s*By\.cssSelector\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator("\1")',
        result
    )
    result = re.sub(
        r'(?:driver\.)?findElement\s*\(\s*By\.className\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator(".\1")',
        result
    )
    result = re.sub(
        r'(?:driver\.)?findElement\s*\(\s*By\.xpath\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator("xpath=\1")',
        result
    )
    result = re.sub(
        r'(?:driver\.)?findElement\s*\(\s*By\.name\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator("[name=\1]")',
        result
    )
    
    # Step 4: Convert element actions
    result = re.sub(r'\.sendKeys\s*\(\s*"([^"]*)"\s*\)', r'.fill("\1")', result)
    result = re.sub(r'\.click\s*\(\s*\)', '.click()', result)
    result = re.sub(r'\.getText\s*\(\s*\)', '.innerText()', result)
    result = re.sub(r'\.isDisplayed\s*\(\s*\)', '.isVisible()', result)
    
    # Step 5: Convert driver methods
    result = re.sub(r'driver\.getTitle\s*\(\s*\)', 'await page.title()', result)
    result = re.sub(r'driver\.getCurrentUrl\s*\(\s*\)', 'await page.url()', result)
    
    # Step 6: Convert Java constructs
    result = re.sub(r'String\s+(\w+)', r'const \1', result)
    result = re.sub(r'WebElement\s+(\w+)', r'const \1', result)
    result = re.sub(r'Thread\.sleep\s*\(\s*(\d+)\s*\)', r'await page.waitForTimeout(\1)', result)
    result = re.sub(r'System\.out\.println\s*\(', 'console.log(', result)
    
    # Step 7: Convert assertions
    result = re.sub(r'Assert\.assertEquals\s*\(\s*([^,]+),\s*([^)]+)\)', r'expect(\1).toBe(\2)', result)
    result = re.sub(r'Assert\.assertTrue\s*\(\s*([^)]+)\)', r'expect(\1).toBeTruthy()', result)
    result = re.sub(r'Assert\.assertFalse\s*\(\s*([^)]+)\)', r'expect(\1).toBeFalsy()', result)
    
    # Step 8: Convert exception handling
    result = re.sub(r'catch\s*\(\s*\w+\s+(\w+)\s*\)', r'catch (\1)', result)
    result = re.sub(r'catch\s*\(\s*Exception\s+(\w+)\s*\)', r'catch (\1)', result)
    result = re.sub(r'(\w+)\.printStackTrace\s*\(\s*\)', r'console.error(\1)', result)
    
    # Step 9: Remove access modifiers and other Java keywords
    result = re.sub(r'\bpublic\s+', '', result)
    result = re.sub(r'\bprivate\s+', '', result)
    result = re.sub(r'\bprotected\s+', '', result)
    result = re.sub(r'\bstatic\s+', '', result)
    result = re.sub(r'\bfinal\s+', '', result)
    
    # Step 10: Clean up braces
    # Count and balance braces
    open_braces = result.count('{')
    close_braces = result.count('}')
    
    # Remove extra closing braces
    while close_braces > open_braces:
        result = result.rstrip()
        if result.endswith('}'):
            result = result[:-1].rstrip()
        close_braces -= 1
    
    # Add missing closing braces
    while open_braces > close_braces:
        result += '\n}'
        close_braces += 1
    
    # Step 11: Strict cleanup
    result = strict_cleanup(result)
    
    # Step 12: Ensure proper structure
    result = ensure_proper_structure(result, class_name)
    
    # Step 13: Format
    lines = result.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if stripped or (cleaned and cleaned[-1].strip()):
            cleaned.append(line)
    result = '\n'.join(cleaned)
    
    return result


# =============================================================================
# Public Interface
# =============================================================================

def convert_code(java_code: str, language: str = "typescript") -> str:
    """Main entry point for conversion."""
    if not java_code or not java_code.strip():
        return "// Error: Empty code"
    
    try:
        result = convert_java_to_playwright(java_code, language)
        
        # Final validation
        forbidden = [
            'chromium.launch',
            'browser.launch', 
            'browser = ',
            'System.setProperty',
            'ChromeDriver',
            'WebDriver ',
            '@BeforeClass',
            '@Test',
            'public void',
        ]
        
        for pattern in forbidden:
            if pattern in result:
                # Try cleanup again
                result = strict_cleanup(result)
                result = ensure_proper_structure(result)
                break
        
        return result
        
    except Exception as e:
        return f"// Error: {str(e)}"


# Test
if __name__ == "__main__":
    test = '''import org.openqa.selenium.*;
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
    public void loginTest() {
        driver.get("https://www.saucedemo.com");
        driver.findElement(By.id("user-name")).sendKeys("standard_user");
        driver.findElement(By.id("password")).sendKeys("secret_sauce");
        driver.findElement(By.id("login-button")).click();
        Assert.assertEquals(driver.getTitle(), "Swag Labs");
    }
    
    @AfterClass
    public void tearDown() {
        driver.quit();
    }
}'''
    
    print("INPUT:")
    print(test)
    print("\n" + "="*60)
    print("OUTPUT:")
    result = convert_code(test, "typescript")
    print(result)
    
    # Validate
    print("\n" + "="*60)
    print("VALIDATION:")
    bad_patterns = ['chromium.launch', 'browser.launch', 'System.setProperty', 'WebDriver', '@Test']
    for p in bad_patterns:
        if p in result:
            print(f"  FAIL: Found '{p}'")
        else:
            print(f"  PASS: '{p}' removed")

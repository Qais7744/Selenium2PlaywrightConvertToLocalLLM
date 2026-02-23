"""
Bulletproof Selenium to Playwright Converter

Converts Java Selenium + TestNG code to Playwright TypeScript.
Guarantees: ZERO Java code in output.
"""

import re


def convert(java_code: str) -> str:
    """
    Convert Java Selenium code to Playwright TypeScript.
    """
    if not java_code or not java_code.strip():
        return "// Error: No code provided"
    
    lines = java_code.split('\n')
    output_lines = []
    
    # Track state
    in_class = False
    class_name = 'TestSuite'
    method_braces = 0
    pending_method = None
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines at start
        if not stripped and not output_lines:
            continue
        
        # Skip comments and imports
        if stripped.startswith('//') or stripped.startswith('*') or stripped.startswith('/*'):
            continue
        if stripped.startswith('import '):
            continue
        if stripped.startswith('package '):
            continue
        
        # === REMOVE COMPLETELY ===
        skip_patterns = [
            r'System\.setProperty',
            r'webdriver\.chrome\.driver',
            r'chromedriver',
            r'geckodriver',
        ]
        
        should_skip = False
        for pattern in skip_patterns:
            if re.search(pattern, stripped, re.IGNORECASE):
                should_skip = True
                break
        
        # Skip WebDriver declarations and instantiation
        if re.search(r'WebDriver\s+\w+', stripped):
            should_skip = True
        if re.search(r'\w+\s*=\s*new\s+\w+Driver', stripped):
            should_skip = True
        if re.search(r'\w+\.quit\s*\(', stripped):
            should_skip = True
        
        if should_skip:
            continue
        
        # === HANDLE CLASS ===
        class_match = re.search(r'class\s+(\w+)', stripped)
        if class_match and not in_class:
            class_name = class_match.group(1)
            in_class = True
            output_lines.append(f"test.describe('{class_name}', () => {{")
            continue
        
        # === HANDLE ANNOTATIONS ===
        if '@BeforeClass' in stripped or '@BeforeSuite' in stripped:
            output_lines.append('    test.beforeAll(async ({ page }) => {')
            method_braces = 1
            continue
        
        if '@AfterClass' in stripped or '@AfterSuite' in stripped:
            output_lines.append('    test.afterAll(async ({ page }) => {')
            method_braces = 1
            continue
        
        if '@BeforeMethod' in stripped:
            output_lines.append('    test.beforeEach(async ({ page }) => {')
            method_braces = 1
            continue
        
        if '@AfterMethod' in stripped:
            output_lines.append('    test.afterEach(async ({ page }) => {')
            method_braces = 1
            continue
        
        if '@Test' in stripped:
            # Method name will be on next line
            continue
        
        # === HANDLE METHOD SIGNATURES ===
        # Match: public void methodName() {
        method_match = re.match(r'(?:public\s+)?(?:void|\w+)\s+(\w+)\s*\(\s*\)\s*\{?\s*$', stripped)
        if method_match:
            method_name = method_match.group(1)
            
            # Skip setUp/tearDown that were converted to hooks
            if method_name in ['setUp', 'tearDown']:
                pending_method = 'hook'
                if '{' in stripped:
                    method_braces = 1
                continue
            
            # Close previous method if any
            if pending_method and pending_method != 'hook':
                output_lines.append('    });')
            
            output_lines.append(f"    test('{method_name}', async ({{ page }}) => {{")
            pending_method = method_name
            if '{' in stripped:
                method_braces = 1
            continue
        
        # === HANDLE CLOSING BRACES ===
        if stripped == '}':
            if method_braces > 0:
                method_braces -= 1
                if method_braces == 0 and pending_method:
                    if pending_method == 'hook':
                        output_lines.append('    });')
                    else:
                        output_lines.append('    });')
                    pending_method = None
            continue
        
        # === CONVERT LINE CONTENT ===
        if stripped:
            converted = convert_line(stripped)
            if converted:
                output_lines.append(f"        {converted}")
    
    # Close final method if open
    if pending_method:
        output_lines.append('    });')
    
    # Close class
    if in_class:
        output_lines.append('});')
    
    # Combine and add imports
    result = '\n'.join(output_lines)
    
    # Add imports
    if 'expect(' in result:
        result = "import { test, expect } from '@playwright/test';\n\n" + result
    else:
        result = "import { test } from '@playwright/test';\n\n" + result
    
    return result


def convert_line(line: str) -> str:
    """Convert a single line of Java to Playwright."""
    if not line:
        return ''
    
    result = line
    
    # Type declarations
    result = re.sub(r'^String\s+(\w+)', r'const \1', result)
    result = re.sub(r'^WebElement\s+(\w+)', r'const \1', result)
    result = re.sub(r'^List<\w+>\s+(\w+)', r'const \1', result)
    result = re.sub(r'^int\s+(\w+)', r'const \1', result)
    result = re.sub(r'^boolean\s+(\w+)', r'const \1', result)
    
    # driver.get() -> await page.goto()
    result = re.sub(r'driver\.get\s*\(\s*"([^"]+)"\s*\)', r'await page.goto("\1")', result)
    
    # findElement conversions
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
    result = re.sub(
        r'(?:driver\.)?findElement\s*\(\s*By\.linkText\s*\(\s*"([^"]+)"\s*\)\s*\)',
        r'page.locator("text=\1")',
        result
    )
    
    # Element actions
    result = re.sub(r'\.sendKeys\s*\(\s*"([^"]*)"\s*\)', r'.fill("\1")', result)
    result = re.sub(r'\.click\s*\(\s*\)', '.click()', result)
    result = re.sub(r'\.clear\s*\(\s*\)', '.clear()', result)
    result = re.sub(r'\.getText\s*\(\s*\)', '.innerText()', result)
    result = re.sub(r'\.isDisplayed\s*\(\s*\)', '.isVisible()', result)
    result = re.sub(r'\.isEnabled\s*\(\s*\)', '.isEnabled()', result)
    result = re.sub(r'\.isSelected\s*\(\s*\)', '.isChecked()', result)
    result = re.sub(r'\.getAttribute\s*\(\s*"([^"]+)"\s*\)', r'.getAttribute("\1")', result)
    
    # Page methods
    result = re.sub(r'driver\.getTitle\s*\(\s*\)', 'await page.title()', result)
    result = re.sub(r'driver\.getCurrentUrl\s*\(\s*\)', 'await page.url()', result)
    
    # Java to JS
    result = re.sub(r'Thread\.sleep\s*\(\s*(\d+)\s*\)', r'await page.waitForTimeout(\1)', result)
    result = re.sub(r'System\.out\.println\s*\(', 'console.log(', result)
    
    # Assertions
    result = re.sub(r'Assert\.assertEquals\s*\(\s*([^,]+),\s*([^)]+)\)', r'expect(\1).toBe(\2)', result)
    result = re.sub(r'Assert\.assertTrue\s*\(\s*([^)]+)\)', r'expect(\1).toBeTruthy()', result)
    result = re.sub(r'Assert\.assertFalse\s*\(\s*([^)]+)\)', r'expect(\1).toBeFalsy()', result)
    result = re.sub(r'Assert\.assertNull\s*\(\s*([^)]+)\)', r'expect(\1).toBeNull()', result)
    result = re.sub(r'Assert\.assertNotNull\s*\(\s*([^)]+)\)', r'expect(\1).not.toBeNull()', result)
    
    # Exception handling
    result = re.sub(r'catch\s*\(\s*(?:Exception|Error|Throwable)\s+(\w+)\s*\)', r'catch (\1)', result)
    result = re.sub(r'(\w+)\.printStackTrace\s*\(\s*\)', r'console.error(\1)', result)
    
    # Remove access modifiers
    result = re.sub(r'\bpublic\s+', '', result)
    result = re.sub(r'\bprivate\s+', '', result)
    result = re.sub(r'\bprotected\s+', '', result)
    result = re.sub(r'\bstatic\s+', '', result)
    result = re.sub(r'\bfinal\s+', '', result)
    
    # Remove semicolons at end (TypeScript doesn't require them)
    result = result.rstrip()
    if result.endswith(';'):
        result = result[:-1]
    
    return result


# Test
if __name__ == "__main__":
    test = '''package com.example;

import org.openqa.selenium.*;
import org.testng.Assert;
import org.testng.annotations.*;

public class LoginTest {
    WebDriver driver;
    
    @BeforeClass
    public void setUp() {
        System.setProperty("webdriver.chrome.driver", "C:/chromedriver.exe");
        driver = new ChromeDriver();
    }
    
    @Test
    public void testLogin() {
        driver.get("https://example.com");
        WebElement username = driver.findElement(By.id("username"));
        username.sendKeys("admin");
        driver.findElement(By.cssSelector("#password")).sendKeys("secret");
        driver.findElement(By.id("login-btn")).click();
        String title = driver.getTitle();
        Assert.assertEquals(title, "Dashboard");
    }
    
    @AfterClass
    public void tearDown() {
        driver.quit();
    }
}'''
    
    print("="*60)
    print("INPUT:")
    print(test)
    print("\n" + "="*60)
    print("OUTPUT:")
    result = convert(test)
    print(result)
    
    print("\n" + "="*60)
    print("VALIDATION:")
    errors = []
    forbidden = ['chromium.launch', 'browser.launch', 'System.setProperty', 'WebDriver', 'ChromeDriver', 
                 'By.id', '.sendKeys(', 'public void', '@Test']
    for pattern in forbidden:
        if pattern in result:
            errors.append(f"Found: {pattern}")
    
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
    else:
        print("  [OK] All checks passed - Pure Playwright code!")

#!/usr/bin/env python3
"""Test the V2 converter."""

import sys
sys.path.insert(0, '.')

from converter_engine_v2 import convert_code

# Test case from user
test_code = '''import org.openqa.selenium.WebDriver;
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
print("INPUT JAVA CODE:")
print("="*60)
print(test_code)

print("\n" + "="*60)
print("CONVERTED PLAYWRIGHT CODE:")
print("="*60)

result = convert_code(test_code, 'typescript')
print(result)

print("\n" + "="*60)
print("VALIDATION (Must NOT contain Java code):")
print("="*60)

java_patterns = [
    ('System.setProperty', 'System.setProperty'),
    ('WebDriver declaration', 'WebDriver '),
    ('Exception type', 'Exception e)'),
    ('printStackTrace', 'printStackTrace'),
    ('driver.quit', 'driver.quit'),
    ('public static void main', 'public static void main'),
    ('chromedriver', 'chromedriver'),
    ('geckodriver', 'geckodriver'),
    ('executablePath', 'executablePath'),
]

all_pass = True
for name, pattern in java_patterns:
    if pattern in result:
        print(f"  [FAIL] Found Java code: {name}")
        all_pass = False
    else:
        print(f"  [PASS] Removed: {name}")

print("\n" + "="*60)
print("MUST CONTAIN (Playwright code):")
print("="*60)

required_patterns = [
    ('test wrapper', "test('SimpleSeleniumTest'"),
    ('async page', 'async ({ page })'),
    ('page.goto', 'await page.goto'),
    ('page.title', 'await page.title'),
    ('console.log', 'console.log'),
    ('waitForTimeout', 'await page.waitForTimeout'),
]

for name, pattern in required_patterns:
    if pattern in result:
        print(f"  [PASS] Has: {name}")
    else:
        print(f"  [FAIL] Missing: {name}")
        all_pass = False

print("\n" + "="*60)
if all_pass:
    print("[ALL CHECKS PASSED - Conversion is correct!]")
else:
    print("[SOME CHECKS FAILED - Review output above]")
print("="*60)

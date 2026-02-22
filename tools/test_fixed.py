#!/usr/bin/env python3
"""Test the fixed conversion engine."""

import sys
sys.path.insert(0, '.')

from converter_engine_fixed import convert_code

# Test case from user
test_code = '''import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;

public class Test {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        driver.get("https://www.google.com");
        System.out.println(driver.getTitle());
        driver.quit();
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
print("VERIFICATION:")
print("="*60)

# Check for correct patterns
checks = [
    ("Has imports", "import { test, expect }" in result or "import { test," in result),
    ("Has test wrapper", "test('" in result and "async ({ page })" in result),
    ("Uses page.goto", "await page.goto" in result),
    ("Uses console.log", "console.log" in result),
    ("Uses page.title", "await page.title()" in result or "page.title()" in result),
    ("No driver references", "driver." not in result),
    ("No Java syntax", "public static" not in result and "class Test" not in result),
    ("Proper closing", "});" in result),
]

for name, passed in checks:
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name}")

if all(passed for _, passed in checks):
    print("\n[ALL CHECKS PASSED]")
else:
    print("\n[SOME CHECKS FAILED]")

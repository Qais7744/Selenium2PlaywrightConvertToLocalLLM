#!/usr/bin/env python3
"""Test the conversion engine."""

import sys
sys.path.insert(0, '.')

from converter_engine_fast import try_fast_conversion

test_code = '''@Test
public void testLogin() {
    WebDriver driver = new ChromeDriver();
    driver.get("https://example.com/login");
    driver.findElement(By.id("username")).sendKeys("admin");
    driver.findElement(By.id("password")).sendKeys("secret");
    driver.findElement(By.cssSelector("button[type='submit']")).click();
    driver.quit();
}'''

print("="*60)
print("INPUT JAVA CODE:")
print("="*60)
print(test_code)

print("\n" + "="*60)
print("CONVERTED PLAYWRIGHT CODE:")
print("="*60)

result = try_fast_conversion(test_code, 'typescript')
if result:
    print(result)
    print("\n[SUCCESS] Fast conversion working!")
else:
    print("[ERROR] Fast conversion returned None")

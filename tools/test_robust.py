#!/usr/bin/env python3
"""Test the robust converter."""

import sys
sys.path.insert(0, '.')

from converter_engine_robust import convert_code

# Test case with all the issues mentioned
test_code = '''import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.By;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.*;

public class SauceDemoTest {
    WebDriver driver;
    
    @BeforeClass
    public void setUp() {
        System.setProperty("webdriver.chrome.driver", "path/to/chromedriver");
        driver = new ChromeDriver();
    }
    
    @Test(priority = 1)
    public void homePageTitleCheck() {
        driver.get("https://www.saucedemo.com");
        String title = driver.getTitle();
        Assert.assertEquals(title, "Swag Labs");
    }
    
    @Test(priority = 2)
    public void loginTest() {
        driver.findElement(By.id("user-name")).sendKeys("standard_user");
        driver.findElement(By.id("password")).sendKeys("secret_sauce");
        driver.findElement(By.id("login-button")).click();
        Assert.assertTrue(driver.getCurrentUrl().contains("inventory"));
    }
    
    @Test(priority = 3)
    public void addToCartTest() {
        driver.findElement(By.id("add-to-cart-sauce-labs-backpack")).click();
        WebElement cartBadge = driver.findElement(By.className("shopping_cart_badge"));
        Assert.assertEquals(cartBadge.getText(), "1");
    }
    
    @AfterClass
    public void tearDown() {
        driver.quit();
    }
}'''

print("="*60)
print("INPUT JAVA SELENIUM + TESTNG CODE:")
print("="*60)
print(test_code)

print("\n" + "="*60)
print("CONVERTED PLAYWRIGHT CODE:")
print("="*60)

result = convert_code(test_code, 'typescript')
print(result)

print("\n" + "="*60)
print("VALIDATION - MUST NOT CONTAIN:")
print("="*60)

forbidden = [
    ('chromium.launch', 'chromium.launch'),
    ('browser.launch', 'browser.launch'),
    ('browser =', 'browser ='),
    ('System.setProperty', 'System.setProperty'),
    ('chromedriver', 'chromedriver'),
    ('ChromeDriver', 'ChromeDriver'),
    ('WebDriver', 'WebDriver'),
    ('@BeforeClass', '@BeforeClass'),
    ('@Test', '@Test'),
    ('public void', 'public void'),
    ('By.id', 'By.id'),
    ('.sendKeys', '.sendKeys'),
    ('.getText', '.getText'),
]

all_pass = True
for name, pattern in forbidden:
    if pattern in result:
        print(f"  [FAIL] Found: {name}")
        all_pass = False
    else:
        print(f"  [PASS] Removed: {name}")

print("\n" + "="*60)
print("VALIDATION - MUST CONTAIN:")
print("="*60)

required = [
    ("import from @playwright/test", "from '@playwright/test'"),
    ("test.describe", "test.describe"),
    ("test()", "test('"),
    ("async ({ page })", "async ({ page })"),
    ("await page.goto", "await page.goto"),
    ("page.locator", "page.locator"),
    ("expect()", "expect("),
]

for name, pattern in required:
    if pattern in result:
        print(f"  [PASS] Has: {name}")
    else:
        print(f"  [FAIL] Missing: {name}")
        all_pass = False

print("\n" + "="*60)
if all_pass:
    print("[ALL CHECKS PASSED - Zero Java code!]")
else:
    print("[SOME CHECKS FAILED]")
print("="*60)

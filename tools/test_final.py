#!/usr/bin/env python3
"""Test the final converter with comprehensive framework conversion."""

import sys
sys.path.insert(0, '.')

from converter_engine_final import convert_code

# Test case: SauceDemo with TestNG framework
test_code = '''import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
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
        WebElement username = driver.findElement(By.id("user-name"));
        username.sendKeys("standard_user");
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
print("VALIDATION - MUST NOT CONTAIN (Java code):")
print("="*60)

java_patterns = [
    ('System.setProperty', 'System.setProperty'),
    ('WebDriver declaration', 'WebDriver '),
    ('chromedriver', 'chromedriver'),
    ('@BeforeClass annotation', '@BeforeClass'),
    ('@AfterClass annotation', '@AfterClass'),
    ('public void', 'public void'),
    ('driver.quit', 'driver.quit'),
    ('driver = new', 'driver = new'),
]

all_pass = True
for name, pattern in java_patterns:
    if pattern in result:
        print(f"  [FAIL] Found Java code: {name}")
        all_pass = False
    else:
        print(f"  [PASS] Removed: {name}")

print("\n" + "="*60)
print("VALIDATION - MUST CONTAIN (Playwright code):")
print("="*60)

required_patterns = [
    ('Playwright import', "from '@playwright/test'"),
    ('test.describe', 'test.describe'),
    ('test.beforeAll', 'test.beforeAll'),
    ('test.afterAll', 'test.afterAll'),
    ('test() wrapper', "test('"),
    ('async page', 'async ({ page })'),
    ('page.goto', 'await page.goto'),
    ('page.locator', 'page.locator'),
    ('.fill()', '.fill('),
    ('.click()', '.click()'),
    ('expect()', 'expect('),
    ('.toBe(', '.toBe('),
]

for name, pattern in required_patterns:
    if pattern in result:
        print(f"  [PASS] Has: {name}")
    else:
        print(f"  [FAIL] Missing: {name}")
        all_pass = False

print("\n" + "="*60)
if all_pass:
    print("[ALL CHECKS PASSED - Framework conversion is correct!]")
else:
    print("[SOME CHECKS FAILED - Review output above]")
print("="*60)

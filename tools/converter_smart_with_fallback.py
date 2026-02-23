"""
Smart Converter with LLM + Fallback

Uses LLM first, falls back to pattern matching if LLM times out.
"""

import re
import requests
from typing import Dict, Any


def pattern_convert(java_code: str) -> str:
    """Fast pattern-based conversion as fallback."""
    result = java_code
    
    # Remove Java boilerplate
    result = re.sub(r'package\s+[\w.]+;', '', result)
    result = re.sub(r'import\s+[^;]+;', '', result)
    result = re.sub(r'System\.setProperty\s*\([^)]+\);', '', result)
    result = re.sub(r'WebDriver\s+\w+\s*=\s*new\s+\w+Driver\s*\([^)]*\);', '', result)
    result = re.sub(r'\w+\.quit\s*\(\s*\);', '', result)
    
    # Convert class
    class_match = re.search(r'class\s+(\w+)', result)
    class_name = class_match.group(1) if class_match else 'Test'
    result = re.sub(r'class\s+\w+\s*\{', '', result)
    
    # Convert main method
    result = re.sub(
        r'public\s+static\s+void\s+main\s*\([^)]*\)\s*\{',
        "test('main', async ({ page }) => {",
        result
    )
    
    # Convert other methods
    result = re.sub(
        r'(?:public\s+)?(?:void|\w+)\s+(\w+)\s*\(\s*\)\s*\{',
        r"test('\1', async ({ page }) => {",
        result
    )
    
    # Convert Selenium to Playwright
    result = re.sub(r'driver\.get\s*\(\s*"([^"]+)"\s*\)', r'await page.goto("\1")', result)
    result = re.sub(r'By\.id\s*\(\s*"([^"]+)"\s*\)', r'"#\1"', result)
    result = re.sub(r'By\.cssSelector\s*\(\s*"([^"]+)"\s*\)', r'"\1"', result)
    result = re.sub(r'By\.className\s*\(\s*"([^"]+)"\s*\)', r'".\1"', result)
    result = re.sub(r'findElement\s*\(', 'page.locator(', result)
    result = re.sub(r'\.sendKeys\s*\(', '.fill(', result)
    result = re.sub(r'\.click\s*\(\s*\)', '.click()', result)
    result = re.sub(r'\.getText\s*\(\s*\)', '.innerText()', result)
    result = re.sub(r'driver\.getTitle\s*\(\s*\)', 'await page.title()', result)
    result = re.sub(r'Thread\.sleep\s*\(\s*(\d+)\s*\)', r'await page.waitForTimeout(\1)', result)
    result = re.sub(r'System\.out\.println\s*\(', 'console.log(', result)
    result = re.sub(r'Assert\.assertEquals\s*\(\s*([^,]+),\s*([^)]+)\)', r'expect(\1).toBe(\2)', result)
    result = re.sub(r'Assert\.assertTrue\s*\(\s*([^)]+)\)', r'expect(\1).toBeTruthy()', result)
    
    # Remove Java keywords
    result = re.sub(r'\bpublic\s+', '', result)
    result = re.sub(r'\bstatic\s+', '', result)
    result = re.sub(r'\bvoid\s+', '', result)
    result = re.sub(r'String\s+(\w+)', r'const \1', result)
    result = re.sub(r'WebElement\s+(\w+)', r'const \1', result)
    
    # Clean up braces
    result = result.replace('}', '});').replace('}};', '});');
    
    # Wrap in describe
    result = f"test.describe('{class_name}', () => {{\n{result}\n}});"
    
    # Add imports
    result = "import { test, expect } from '@playwright/test';\n\n" + result
    
    return result


def create_prompt(java_code: str, language: str) -> str:
    """Create LLM prompt."""
    lang = "TypeScript" if language == "typescript" else "JavaScript"
    
    return f"""Convert Java Selenium to Playwright {lang}.

RULES:
1. Use: import {{ test, expect }} from '@playwright/test'
2. NEVER use: chromium.launch() or browser.launch()
3. ALWAYS use: async ({{ page }}) => {{}} fixture
4. Convert driver.get() to await page.goto()
5. Convert findElement(By.id("x")) to page.locator("#x")
6. Convert .sendKeys() to .fill()
7. Convert .click() to .click()
8. Remove: System.setProperty, WebDriver, ChromeDriver, public, static, void

OUTPUT ONLY THE CODE.

Java:
```java
{java_code}
```

Playwright {lang}:"""


def llm_convert(java_code: str, language: str = "typescript") -> Dict[str, Any]:
    """Try LLM conversion with fallback."""
    prompt = create_prompt(java_code, language)
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5-coder:0.5b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 1500,
                }
            },
            timeout=60  # 1 minute timeout
        )
        response.raise_for_status()
        data = response.json()
        code = data.get("response", "")
        
        # Extract code
        match = re.search(r'```(?:typescript|javascript)?\s*\n?(.*?)\n?```', code, re.DOTALL)
        if match:
            code = match.group(1).strip()
        
        # Fix common issues
        code = re.sub(r"import\s*\{\s*chromium\s*\}\s*from\s*['\"]playwright['\"];?\n?", '', code)
        code = re.sub(r'const\s+\w+\s*=\s*await\s+chromium\.launch[^;]*;?', '', code)
        
        if 'from \'@playwright/test\'' not in code:
            code = "import { test, expect } from '@playwright/test';\n\n" + code
        
        return {"status": "success", "converted_code": code, "method": "llm"}
        
    except requests.exceptions.Timeout:
        # LLM timed out, use fallback
        code = pattern_convert(java_code)
        return {
            "status": "success", 
            "converted_code": code, 
            "method": "pattern_fallback",
            "note": "LLM timed out, used pattern matching"
        }
    except Exception as e:
        # Any other error, use fallback
        code = pattern_convert(java_code)
        return {
            "status": "success",
            "converted_code": code,
            "method": "pattern_fallback",
            "note": f"LLM error ({str(e)}), used pattern matching"
        }


if __name__ == "__main__":
    test = '''public class Test {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        driver.get("https://google.com");
        System.out.println(driver.getTitle());
    }
}'''
    print(llm_convert(test, "typescript")['converted_code'])

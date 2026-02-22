"""
Fixed Ultra-Fast Code Converter for Selenium2Playwright

Properly converts Selenium Java to Playwright TypeScript/JavaScript.
"""

import re
import json
import time
import asyncio
import hashlib
from typing import Optional, Dict, Any
from dataclasses import dataclass

import aiohttp
import requests


def try_fast_conversion(java_code: str, language: str = "typescript") -> Optional[str]:
    """
    Convert simple Selenium Java code to Playwright using regex patterns.
    Returns None if code is too complex.
    """
    try:
        code = java_code
        
        # Check if it's simple enough for regex conversion
        # Skip if has complex patterns
        complex_patterns = ['try {', 'catch', 'finally', 'switch', 'case ',
                           'stream()', 'DataProvider', 'for (', 'while (']
        for pattern in complex_patterns:
            if pattern in code:
                return None  # Too complex, use LLM
        
        # Remove Java imports and package
        code = re.sub(r'package\s+[\w.]+;', '', code)
        code = re.sub(r'import\s+[^;]+;', '', code)
        
        # Convert @Test annotation and method signature
        # Pattern: @Test [optional stuff] public void methodName() {
        code = re.sub(
            r'@Test(?:\([^)]*\))?\s*\n\s*public\s+void\s+(\w+)\s*\(\s*\)\s*{',
            r"test('\1', async ({ page }) => {",
            code
        )
        
        # Remove WebDriver setup lines
        code = re.sub(r'\s*WebDriver\s+\w+\s*=\s*new\s+\w+Driver\([^)]*\)\s*;\s*\n?', '\n', code)
        code = re.sub(r'\s*driver\.quit\(\)\s*;\s*\n?', '\n', code)
        
        # Convert driver.get() -> await page.goto()
        code = re.sub(
            r'driver\.get\s*\(\s*"([^"]+)"\s*\)',
            r'await page.goto("\1")',
            code
        )
        
        # Convert findElement(By.id()) -> page.locator()
        code = re.sub(
            r'driver\.findElement\s*\(\s*By\.id\s*\(\s*"([^"]+)"\s*\)\s*\)',
            r'page.locator("#\1")',
            code
        )
        
        # Convert findElement(By.cssSelector()) -> page.locator()
        code = re.sub(
            r'driver\.findElement\s*\(\s*By\.cssSelector\s*\(\s*"([^"]+)"\s*\)\s*\)',
            r'page.locator("\1")',
            code
        )
        
        # Convert findElement(By.xpath()) -> page.locator()
        code = re.sub(
            r'driver\.findElement\s*\(\s*By\.xpath\s*\(\s*"([^"]+)"\s*\)\s*\)',
            r'page.locator("xpath=\1")',
            code
        )
        
        # Convert findElement(By.className()) -> page.locator()
        code = re.sub(
            r'driver\.findElement\s*\(\s*By\.className\s*\(\s*"([^"]+)"\s*\)\s*\)',
            r'page.locator(".\1")',
            code
        )
        
        # Convert findElement(By.name()) -> page.locator()
        code = re.sub(
            r'driver\.findElement\s*\(\s*By\.name\s*\(\s*"([^"]+)"\s*\)\s*\)',
            r'page.locator("[name=\1]")',
            code
        )
        
        # Convert .sendKeys() -> .fill()
        code = re.sub(
            r'\.sendKeys\s*\(\s*"([^"]*)"\s*\)',
            r'.fill("\1")',
            code
        )
        
        # Convert .click() -> .click()
        # (already same, but ensure no extra args)
        code = re.sub(r'\.click\s*\(\s*\)', '.click()', code)
        
        # Convert .getText() -> .innerText()
        code = re.sub(r'\.getText\s*\(\s*\)', '.innerText()', code)
        
        # Add await to page operations
        code = re.sub(r'^(\s+)(page\.locator)', r'\1await \2', code, flags=re.MULTILINE)
        code = re.sub(r'^(\s+)(page\.goto)', r'\1await \2', code, flags=re.MULTILINE)
        
        # Convert Assert.assertEquals -> expect().toBe()
        code = re.sub(
            r'Assert\.assertEquals\s*\(\s*"([^"]+)"\s*,\s*([^)]+)\)',
            r'expect(\2).toBe("\1")',
            code
        )
        
        # Convert Thread.sleep() -> await page.waitForTimeout()
        code = re.sub(
            r'Thread\.sleep\s*\(\s*(\d+)\s*\)',
            r'await page.waitForTimeout(\1)',
            code
        )
        
        # Clean up remaining Java syntax
        code = re.sub(r'\bString\s+(\w+)', r'const \1', code)
        code = re.sub(r'\bWebElement\s+(\w+)', r'const \1', code)
        
        # Remove empty lines
        code = re.sub(r'\n{3,}', '\n\n', code)
        
        # Ensure proper closing brace
        # Count opening and closing braces
        open_braces = code.count('{')
        close_braces = code.count('}')
        
        # Add missing closing braces
        while close_braces < open_braces:
            code = code.rstrip() + '\n}'
            close_braces += 1
        
        # Ensure final }); for test block
        if not code.rstrip().endswith('});'):
            if code.rstrip().endswith('}'):
                code = code.rstrip()[:-1] + '});'
            else:
                code = code.rstrip() + '\n});'
        
        # Add Playwright imports
        is_ts = language.lower() == "typescript"
        if is_ts:
            imports = "import { test, expect } from '@playwright/test';\n\n"
        else:
            imports = "const { test, expect } = require('@playwright/test');\n\n"
        
        final_code = imports + code.strip()
        
        # Validate output
        if 'page.' not in final_code or 'test(' not in final_code:
            return None
        
        return final_code
        
    except Exception as e:
        print(f"Fast conversion error: {e}")
        return None


class FastOllamaClient:
    """Ollama client with connection reuse and model warming."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5-coder:0.5b"):
        self.base_url = base_url
        self.model = model
        self.generate_url = f"{base_url}/api/generate"
        self._session: Optional[aiohttp.ClientSession] = None
        self._model_warmed = False
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create session with optimized settings."""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            timeout = aiohttp.ClientTimeout(total=60, connect=5)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'Connection': 'keep-alive'}
            )
        return self._session
    
    async def warm_up(self):
        """Send a dummy request to warm up the model."""
        if self._model_warmed:
            return
        
        print("🌡️  Warming up model...")
        start = time.time()
        
        try:
            session = await self._get_session()
            payload = {
                "model": self.model,
                "prompt": "// Warmup",
                "stream": False,
                "options": {
                    "temperature": 0,
                    "num_predict": 1,
                }
            }
            
            async with session.post(self.generate_url, json=payload) as response:
                await response.text()
            
            self._model_warmed = True
            print(f"✅ Model warmed up in {time.time()-start:.2f}s")
            
        except Exception as e:
            print(f"⚠️  Warmup failed: {e}")
    
    async def generate(
        self, 
        prompt: str, 
        max_tokens: int = 1024,
        temperature: float = 0.1
    ) -> str:
        """Generate with optimized settings."""
        await self.warm_up()
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_k": 20,
                "top_p": 0.9,
                "repeat_penalty": 1.0,
            }
        }
        
        session = await self._get_session()
        
        async with session.post(self.generate_url, json=payload) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("response", "")
    
    async def close(self):
        """Close session."""
        if self._session and not self._session.closed:
            await self._session.close()


class FastConverter:
    """Fast converter with hybrid approach."""
    
    def __init__(self, model: str = "qwen2.5-coder:0.5b"):
        self.client = FastOllamaClient(model=model)
        self._cache: Dict[str, str] = {}
        self._cache_hits = 0
        self._fast_conversions = 0
        self._llm_conversions = 0
    
    def _get_cache_key(self, code: str, lang: str) -> str:
        """Generate cache key."""
        return hashlib.md5(f"{code}:{lang}".encode()).hexdigest()
    
    def _build_prompt(self, code: str, lang: str) -> str:
        """Build conversion prompt."""
        lang_cap = "TypeScript" if lang == "typescript" else "JavaScript"
        
        return f"""Convert this Selenium Java test to Playwright {lang_cap}:

```java
{code}
```

Conversion rules:
1. Use `test('name', async ({{ page }}) => {{ ... }})` format
2. Use `await page.goto()` for navigation
3. Use `page.locator()` with CSS selectors (e.g., `#id`, `.class`)
4. Use `.fill()` for input, `.click()` for clicking
5. Add proper imports: `import {{ test, expect }} from '@playwright/test'`
6. Return ONLY the code, no explanations

Playwright {lang_cap} code:"""
    
    def _extract_code(self, raw_output: str, language: str) -> str:
        """Extract and clean code from LLM output."""
        result = raw_output.strip()
        
        # Try to extract code blocks
        patterns = [
            r'```(?:typescript|javascript|ts|js)?\s*\n?(.*?)\n?```',
            r'```\s*\n?(.*?)\n?```',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, raw_output, re.DOTALL | re.IGNORECASE)
            if match:
                result = match.group(1).strip()
                break
        
        # Clean up common LLM mistakes
        # Fix double opening braces like {) {
        result = re.sub(r'\{\)\s*\{', ' {', result)
        # Fix misplaced braces in strings
        result = re.sub(r'"([^"]*)"\}', r'"\1")', result)
        result = re.sub(r'\)"\}', ')"', result)
        
        # Add imports if missing
        if 'import' not in result and 'require' not in result:
            if language == "typescript":
                result = "import { test, expect } from '@playwright/test';\n\n" + result
            else:
                result = "const { test, expect } = require('@playwright/test');\n\n" + result
        
        return result
    
    async def convert(self, java_code: str, language: str = "typescript") -> Dict[str, Any]:
        """Convert Java code to Playwright."""
        start = time.time()
        
        # Clean input
        java_code = java_code.strip()
        if not java_code:
            return {
                "status": "error",
                "message": "Empty code provided",
                "time": 0
            }
        
        # 1. Check cache
        cache_key = self._get_cache_key(java_code, language)
        if cache_key in self._cache:
            self._cache_hits += 1
            return {
                "status": "success",
                "converted_code": self._cache[cache_key],
                "method": "cache",
                "time": round(time.time() - start, 3)
            }
        
        # 2. Try fast regex conversion first
        fast_result = try_fast_conversion(java_code, language)
        if fast_result:
            self._fast_conversions += 1
            self._cache[cache_key] = fast_result
            return {
                "status": "success",
                "converted_code": fast_result,
                "method": "fast-regex",
                "time": round(time.time() - start, 3)
            }
        
        # 3. Fall back to LLM for complex cases
        prompt = self._build_prompt(java_code, language)
        
        try:
            raw_output = await self.client.generate(
                prompt, 
                max_tokens=2048,
                temperature=0.1
            )
            
            result = self._extract_code(raw_output, language)
            
            self._llm_conversions += 1
            self._cache[cache_key] = result
            
            return {
                "status": "success",
                "converted_code": result,
                "method": "llm",
                "time": round(time.time() - start, 3)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "time": round(time.time() - start, 3)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get conversion statistics."""
        total = self._cache_hits + self._fast_conversions + self._llm_conversions
        return {
            "total_conversions": total,
            "cache_hits": self._cache_hits,
            "fast_conversions": self._fast_conversions,
            "llm_conversions": self._llm_conversions,
            "cache_hit_rate": round(self._cache_hits / total * 100, 1) if total > 0 else 0,
            "fast_conversion_rate": round(self._fast_conversions / total * 100, 1) if total > 0 else 0,
        }
    
    async def close(self):
        await self.client.close()


# Singleton instance
_converter: Optional[FastConverter] = None


def get_converter() -> FastConverter:
    """Get singleton converter instance."""
    global _converter
    if _converter is None:
        _converter = FastConverter()
    return _converter


def convert_code(java_code: str, language: str = "typescript", **kwargs) -> str:
    """Synchronous interface for compatibility."""
    converter = get_converter()
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(converter.convert(java_code, language))
    
    if result['status'] == 'success':
        return result['converted_code']
    else:
        return f"// Error: {result.get('message', 'Unknown error')}"


if __name__ == "__main__":
    # Test with the example
    test_code = '''@Test
public void testLogin() {
    WebDriver driver = new ChromeDriver();
    driver.get("https://example.com/login");
    driver.findElement(By.id("username")).sendKeys("admin");
    driver.findElement(By.id("password")).sendKeys("secret");
    driver.findElement(By.cssSelector("button[type='submit']")).click();
    driver.quit();
}'''
    
    print("Testing FAST converter...")
    print("="*60)
    print("Input:")
    print(test_code)
    print("\n" + "="*60)
    
    result = convert_code(test_code, "typescript")
    print("\nOutput:")
    print(result)
    print("\n" + "="*60)
    
    stats = get_converter().get_stats()
    print(f"Stats: {stats}")

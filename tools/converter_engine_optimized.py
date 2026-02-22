"""
Optimized Code Converter Engine for Selenium2Playwright

This module provides high-performance code conversion using:
- Async/await for non-blocking operations
- Connection pooling for HTTP requests
- Regex-based pre-processing to reduce LLM load
- Response streaming for faster perceived performance
- Intelligent caching for repeated conversions
- Batch processing support

Author: AI Assistant
"""

import re
import json
import asyncio
import hashlib
import time
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import requests
from functools import lru_cache


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class ConverterConfig:
    """Configuration for the converter engine."""
    ollama_url: str = "http://localhost:11434/api/generate"
    model: str = "qwen2.5-coder:1.5b"
    timeout: int = 120
    max_workers: int = 4
    enable_cache: bool = True
    cache_size: int = 100
    use_streaming: bool = True
    
    # Performance tuning
    connection_pool_size: int = 10
    connection_keep_alive: bool = True


# =============================================================================
# Connection Pool & Session Management
# =============================================================================

class ConnectionManager:
    """Manages HTTP connections with pooling for optimal performance."""
    
    _instance = None
    _session: Optional[requests.Session] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_session(self, pool_size: int = 10) -> requests.Session:
        """Get or create a session with connection pooling."""
        if self._session is None:
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=pool_size,
                pool_maxsize=pool_size,
                max_retries=3,
                pool_block=False
            )
            self._session = requests.Session()
            self._session.mount('http://', adapter)
            self._session.mount('https://', adapter)
        return self._session
    
    def close(self):
        """Close the session and cleanup connections."""
        if self._session:
            self._session.close()
            self._session = None


# =============================================================================
# Intelligent Caching
# =============================================================================

class ConversionCache:
    """LRU Cache for code conversion results with content-based keys."""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_order: List[str] = []
    
    def _generate_key(self, code: str, language: str, model: str) -> str:
        """Generate a cache key from code content and parameters."""
        content = f"{code}:{language}:{model}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def get(self, code: str, language: str, model: str) -> Optional[str]:
        """Get cached result if available."""
        key = self._generate_key(code, language, model)
        if key in self._cache:
            # Move to end (most recently used)
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]['result']
        return None
    
    def set(self, code: str, language: str, model: str, result: str):
        """Cache a conversion result."""
        key = self._generate_key(code, language, model)
        
        # Evict oldest if at capacity
        if len(self._cache) >= self.max_size and key not in self._cache:
            oldest = self._access_order.pop(0)
            del self._cache[oldest]
        
        self._cache[key] = {
            'result': result,
            'timestamp': time.time()
        }
        
        if key not in self._access_order:
            self._access_order.append(key)
    
    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
        self._access_order.clear()


# =============================================================================
# Pre-Processing: Regex-Based Optimizations
# =============================================================================

class CodePreProcessor:
    """Pre-processes Java code to reduce LLM workload and improve speed."""
    
    # Common patterns that can be pre-converted
    SELENIUM_PATTERNS = [
        # Basic findElement conversions (hints for LLM)
        (r'findElement\s*\(\s*By\.id\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\)', 
         r'# Pre-converted: page.locator("#\1")'),
        (r'findElement\s*\(\s*By\.cssSelector\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\)', 
         r'# Pre-converted: page.locator("\1")'),
        (r'findElement\s*\(\s*By\.xpath\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\)', 
         r'# Pre-converted: page.locator("xpath=\1")'),
        (r'findElement\s*\(\s*By\.className\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\)', 
         r'# Pre-converted: page.locator(".\1")'),
        (r'findElement\s*\(\s*By\.name\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\)', 
         r'# Pre-converted: page.locator("[name=\1]")'),
        
        # Common method hints
        (r'\.sendKeys\s*\(', r'.fill('),
        (r'\.click\s*\(\s*\)', r'.click()'),
        (r'\.getText\s*\(\s*\)', r'.innerText()'),
        (r'driver\.get\s*\(', r'page.goto('),
        (r'driver\.quit\s*\(\s*\)', r'# Remove: Playwright handles browser lifecycle'),
    ]
    
    @classmethod
    def clean_java_code(cls, java_code: str) -> str:
        """
        Clean and optimize Java code before sending to LLM.
        Reduces token count and processing time.
        """
        # Remove package declaration
        java_code = re.sub(r'^\s*package\s+[\w\.]+;\s*', '', java_code, flags=re.MULTILINE)
        
        # Remove standard Java imports (keep Selenium/TestNG)
        java_code = re.sub(r'^\s*import\s+java\.[\w\.*]+;\s*$', '', java_code, flags=re.MULTILINE)
        java_code = re.sub(r'^\s*import\s+org\.openqa\.selenium\.[\w\.*]+;\s*$', '', java_code, flags=re.MULTILINE)
        
        # Remove excessive blank lines
        java_code = re.sub(r'\n{3,}', '\n\n', java_code)
        
        # Remove comments that don't add context
        java_code = re.sub(r'^\s*//\s*(TODO|FIXME|NOTE).*$', '', java_code, flags=re.MULTILINE)
        
        return java_code.strip()
    
    @classmethod
    def add_conversion_hints(cls, java_code: str) -> str:
        """
        Add pre-conversion hints to help LLM understand patterns faster.
        This reduces the LLM's reasoning time.
        """
        hinted_code = java_code
        
        for pattern, replacement in cls.SELENIUM_PATTERNS:
            hinted_code = re.sub(pattern, replacement, hinted_code)
        
        return hinted_code


# =============================================================================
# Async Converter Core
# =============================================================================

class AsyncCodeConverter:
    """
    High-performance asynchronous code converter.
    
    Features:
    - Non-blocking async operations
    - Connection pooling
    - Streaming responses for faster feedback
    - Intelligent caching
    """
    
    def __init__(self, config: Optional[ConverterConfig] = None):
        self.config = config or ConverterConfig()
        self.cache = ConversionCache(max_size=self.config.cache_size)
        self.connection_manager = ConnectionManager()
        self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
    
    def _build_prompt(self, cleaned_code: str, language: str) -> str:
        """Build an optimized prompt for the LLM."""
        is_ts = language.lower() == "typescript"
        lang_name = "TypeScript" if is_ts else "JavaScript"
        
        # Concise rules to reduce token count and processing time
        rules = [
            "Use Playwright's async/await pattern",
            "Convert @Test to test('name', async ({ page }) => {...})",
            "Use page.locator() for element selection",
            "Use .fill() instead of .sendKeys()",
            "Use page.goto() instead of driver.get()",
            "Remove browser setup - Playwright handles this",
        ]
        
        if is_ts:
            rules.append("Use TypeScript types (Page, Locator)")
        else:
            rules.append("No TypeScript types - pure JavaScript only")
        
        rules_text = "\n".join(f"{i+1}. {rule}" for i, rule in enumerate(rules))
        
        return f"""Convert Selenium Java to Playwright {lang_name}.

Rules:
{rules_text}

Input:
```java
{cleaned_code}
```

Output {lang_name} code only:"""
    
    async def _convert_async_streaming(
        self, 
        prompt: str, 
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Convert code using streaming for faster perceived performance.
        
        Args:
            prompt: The formatted prompt for the LLM
            progress_callback: Optional callback for streaming updates
            
        Returns:
            The complete converted code
        """
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": 0.1,  # Lower = faster, more deterministic
                "num_predict": 2048,  # Limit output tokens for speed
            }
        }
        
        full_response = []
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.config.ollama_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                response.raise_for_status()
                
                async for line in response.content:
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        chunk = data.get("response", "")
                        full_response.append(chunk)
                        
                        # Call progress callback if provided
                        if progress_callback:
                            progress_callback(chunk)
                        
                        # Check if done
                        if data.get("done", False):
                            break
                            
                    except json.JSONDecodeError:
                        continue
        
        return "".join(full_response)
    
    def _convert_sync(self, prompt: str) -> str:
        """
        Synchronous conversion using connection pooling.
        Falls back to this if streaming fails.
        """
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 2048,
            }
        }
        
        session = self.connection_manager.get_session(
            pool_size=self.config.connection_pool_size
        )
        
        response = session.post(
            self.config.ollama_url,
            json=payload,
            timeout=self.config.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get("response", "")
    
    def _extract_code(self, raw_output: str, language: str) -> str:
        """Extract code block from LLM output."""
        # Try language-specific code block first
        patterns = [
            rf'```{language}\s*(.*?)```',
            r'```typescript\s*(.*?)```',
            r'```javascript\s*(.*?)```',
            r'```js\s*(.*?)```',
            r'```ts\s*(.*?)```',
            r'```\s*(.*?)```',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, raw_output, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback: return raw output stripped
        return raw_output.strip()
    
    async def convert(
        self,
        java_code: str,
        language: str = "typescript",
        progress_callback: Optional[Callable[[str], None]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Convert Java Selenium code to Playwright.
        
        Args:
            java_code: The Java source code to convert
            language: Target language ("typescript" or "javascript")
            progress_callback: Optional callback for streaming progress
            use_cache: Whether to use caching
            
        Returns:
            Dictionary with conversion results and metadata
        """
        start_time = time.time()
        
        # Check cache first
        if use_cache and self.config.enable_cache:
            cached = self.cache.get(java_code, language, self.config.model)
            if cached:
                return {
                    "status": "success",
                    "converted_code": cached,
                    "cached": True,
                    "time_taken": 0.0,
                    "model": self.config.model
                }
        
        # Pre-process code
        cleaned_code = CodePreProcessor.clean_java_code(java_code)
        hinted_code = CodePreProcessor.add_conversion_hints(cleaned_code)
        
        # Build prompt
        prompt = self._build_prompt(hinted_code, language)
        
        try:
            # Try streaming first for better UX
            if self.config.use_streaming:
                try:
                    raw_output = await self._convert_async_streaming(
                        prompt, progress_callback
                    )
                except Exception as e:
                    # Fall back to sync conversion
                    loop = asyncio.get_event_loop()
                    raw_output = await loop.run_in_executor(
                        self._executor, self._convert_sync, prompt
                    )
            else:
                loop = asyncio.get_event_loop()
                raw_output = await loop.run_in_executor(
                    self._executor, self._convert_sync, prompt
                )
            
            # Extract code
            converted_code = self._extract_code(raw_output, language)
            
            # Cache result
            if use_cache and self.config.enable_cache:
                self.cache.set(java_code, language, self.config.model, converted_code)
            
            time_taken = time.time() - start_time
            
            return {
                "status": "success",
                "converted_code": converted_code,
                "cached": False,
                "time_taken": round(time_taken, 2),
                "model": self.config.model
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "time_taken": round(time.time() - start_time, 2)
            }
    
    async def convert_batch(
        self,
        code_snippets: List[Dict[str, str]],
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Convert multiple code snippets concurrently.
        
        Args:
            code_snippets: List of dicts with 'code' and 'language' keys
            max_concurrent: Maximum number of concurrent conversions
            
        Returns:
            List of conversion results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def convert_with_limit(item: Dict[str, str]) -> Dict[str, Any]:
            async with semaphore:
                return await self.convert(
                    java_code=item['code'],
                    language=item.get('language', 'typescript')
                )
        
        tasks = [convert_with_limit(item) for item in code_snippets]
        return await asyncio.gather(*tasks)
    
    def close(self):
        """Cleanup resources."""
        self._executor.shutdown(wait=True)
        self.connection_manager.close()


# =============================================================================
# Backward Compatible Interface
# =============================================================================

# Global converter instance (singleton for caching benefits)
_converter_instance: Optional[AsyncCodeConverter] = None


def get_converter(config: Optional[ConverterConfig] = None) -> AsyncCodeConverter:
    """Get or create the global converter instance."""
    global _converter_instance
    if _converter_instance is None:
        _converter_instance = AsyncCodeConverter(config)
    return _converter_instance


def convert_code(java_code: str, language: str = "typescript", **kwargs) -> str:
    """
    Backward-compatible synchronous conversion function.
    
    This is the main entry point that maintains compatibility with existing code.
    Internally uses async for better performance.
    
    Args:
        java_code: Java source code to convert
        language: Target language ("typescript" or "javascript")
        **kwargs: Additional options
            - model: Override default model
            - timeout: Request timeout in seconds
            - use_cache: Whether to use caching (default: True)
            
    Returns:
        Converted code string (or error message starting with "// Error")
    """
    config = ConverterConfig()
    if 'model' in kwargs:
        config.model = kwargs['model']
    if 'timeout' in kwargs:
        config.timeout = kwargs['timeout']
    if 'use_cache' in kwargs:
        config.enable_cache = kwargs['use_cache']
    
    converter = get_converter(config)
    
    try:
        # Run async function in sync context
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            converter.convert(java_code, language, use_cache=config.enable_cache)
        )
        
        if result['status'] == 'success':
            return result['converted_code']
        else:
            return f"// Error converting code: {result.get('message', 'Unknown error')}"
            
    except Exception as e:
        return f"// Error converting code: {str(e)}"


# Maintain backward compatibility with old import
clean_java_code = CodePreProcessor.clean_java_code


# =============================================================================
# Fast Model Options
# =============================================================================

FAST_MODELS = {
    "ultra_fast": "qwen2.5-coder:0.5b",  # Fastest, less accurate
    "fast": "qwen2.5-coder:1.5b",        # Good balance (default)
    "balanced": "codellama:7b",          # Better quality
    "accurate": "codellama:13b",         # Best quality, slower
}


def set_model_speed_level(level: str = "fast"):
    """
    Change model for speed/quality trade-off.
    
    Args:
        level: One of "ultra_fast", "fast", "balanced", "accurate"
    """
    global _converter_instance
    if level in FAST_MODELS:
        config = ConverterConfig(model=FAST_MODELS[level])
        _converter_instance = AsyncCodeConverter(config)
        return FAST_MODELS[level]
    raise ValueError(f"Unknown speed level: {level}")


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    # Test conversion
    test_code = """
    @Test
    public void testLogin() {
        WebDriver driver = new ChromeDriver();
        driver.get("https://example.com");
        driver.findElement(By.id("username")).sendKeys("admin");
        driver.findElement(By.id("password")).sendKeys("secret");
        driver.findElement(By.cssSelector("button[type='submit']")).click();
        driver.quit();
    }
    """
    
    print("Testing optimized converter...")
    
    # Time the conversion
    import time
    start = time.time()
    result = convert_code(test_code, language="typescript")
    elapsed = time.time() - start
    
    print(f"\nConversion completed in {elapsed:.2f}s")
    print(f"\nResult:\n{result}")

#!/usr/bin/env python3
"""
Speed Diagnostic Tool for Selenium2Playwright

Identifies bottlenecks in the conversion pipeline.
"""

import time
import requests
import sys

BASE_URL = "http://localhost:5000"

TEST_CODE = """
@Test
public void testLogin() {
    WebDriver driver = new ChromeDriver();
    driver.get("https://example.com/login");
    driver.findElement(By.id("username")).sendKeys("admin");
    driver.findElement(By.id("password")).sendKeys("secret");
    driver.findElement(By.cssSelector("button[type='submit']")).click();
    driver.quit();
}
"""


def check_ollama():
    """Check Ollama connection speed."""
    print("\n🔍 Checking Ollama connection...")
    
    try:
        start = time.time()
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            print(f"  ✅ Ollama reachable in {elapsed:.3f}s")
            print(f"  📦 Models: {', '.join(models[:3])}")
            return True
        else:
            print(f"  ❌ Ollama returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("  ❌ Cannot connect to Ollama on port 11434")
        print("     Run: ollama serve")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def check_converter_app():
    """Check if converter app is running."""
    print("\n🔍 Checking converter app...")
    
    try:
        start = time.time()
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ App reachable in {elapsed:.3f}s")
            print(f"  🔧 Mode: {data.get('converter', 'unknown')}")
            return True
        else:
            print(f"  ⚠️  App returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Cannot connect to app: {e}")
        print(f"     Make sure to run: python tools/app_fast.py")
        return False


def benchmark_conversion():
    """Benchmark actual conversion."""
    print("\n🔍 Benchmarking conversion...")
    
    # Clear cache first
    try:
        requests.post(f"{BASE_URL}/cache/clear", timeout=5)
    except:
        pass
    
    # Cold conversion
    print("  Testing cold conversion...")
    start = time.time()
    response = requests.post(
        f"{BASE_URL}/convert",
        json={"source_code": TEST_CODE, "language": "typescript"},
        timeout=120
    )
    cold_time = time.time() - start
    
    if response.status_code == 200:
        data = response.json()
        method = data.get('method', 'unknown')
        print(f"  ✅ Cold conversion: {cold_time:.2f}s (method: {method})")
    else:
        print(f"  ❌ Conversion failed: {response.text}")
        return
    
    # Cached conversion
    print("  Testing cached conversion...")
    start = time.time()
    response = requests.post(
        f"{BASE_URL}/convert",
        json={"source_code": TEST_CODE, "language": "typescript"},
        timeout=10
    )
    cached_time = time.time() - start
    
    if response.status_code == 200:
        print(f"  ✅ Cached conversion: {cached_time:.3f}s")
        speedup = cold_time / cached_time if cached_time > 0 else 0
        print(f"  📊 Cache speedup: {speedup:.1f}x")


def analyze_bottleneck():
    """Analyze where the bottleneck is."""
    print("\n" + "="*50)
    print("          BOTTLENECK ANALYSIS")
    print("="*50)
    
    issues = []
    recommendations = []
    
    # Check Ollama
    print("\n1. Checking Ollama...")
    if not check_ollama():
        issues.append("Ollama not running")
        recommendations.append("Start Ollama: ollama serve")
    
    # Check app
    print("\n2. Checking converter app...")
    if not check_converter_app():
        issues.append("Converter app not running")
        recommendations.append("Start app: python tools/app_fast.py")
        return
    
    # Benchmark
    print("\n3. Running benchmarks...")
    benchmark_conversion()
    
    # Summary
    print("\n" + "="*50)
    print("          RECOMMENDATIONS")
    print("="*50)
    
    if not issues:
        print("\n✅ All systems operational!")
        print("\nTo improve speed further:")
        print("  1. Use FAST mode: python tools/app_fast.py")
        print("  2. Use smaller model: ollama pull qwen2.5-coder:0.5b")
        print("  3. Enable GPU if available")
        print("  4. Split large test files into smaller chunks")
    else:
        print("\n❌ Issues found:")
        for issue in issues:
            print(f"   • {issue}")
        
        print("\n🔧 Fix these:")
        for rec in recommendations:
            print(f"   • {rec}")


def main():
    print("="*50)
    print("  SELENIUM2PLAYWRIGHT - SPEED DIAGNOSTIC")
    print("="*50)
    
    try:
        analyze_bottleneck()
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnostic interrupted")
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*50)


if __name__ == "__main__":
    main()

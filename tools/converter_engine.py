import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:1.5b"

def clean_java_code(java_code):
    """
    Basic cleanup of Java code before sending to LLM.
    Removes package declarations and excessive imports to save tokens.
    """
    # Remove package declaration
    java_code = re.sub(r'package\s+[\w\.]+;', '', java_code)
    
    # Remove standard library imports (keep selenium/testng)
    java_code = re.sub(r'import\s+java\.[\w\.]+\.*;', '', java_code)
    
    return java_code.strip()

def convert_code(java_code, language="typescript", model="codellama"):
    """
    Sends cleaned Java code to Ollama for conversion to Playwright.
    """
    cleaned_code = clean_java_code(java_code)
    
    is_ts = language.lower() == "typescript"
    lang_name = "TypeScript" if is_ts else "JavaScript"
    
    # Common Rules
    rules = [
        "**Async/Await**: Playwright is async. All interactions must be awaited.",
        "**Locators**: Convert `By.id(\"foo\")` to `page.locator(\"#foo\")`.",
        f"**Test Runner**: Convert `@Test` to `test('name', async ({{ page }}) => {{ ... }})`.",
        "**No Hallucinations**: If you don't know a library, leave a TODO comment.",
        "**NO SELENIUM**: Do NOT import `selenium-webdriver` or use `ChromeDriver`. Use Playwright's native `page` fixture.",
        "**Browser Setup**: Do NOT set up the browser manually. Playwright handles this via `test` fixtures."
    ]

    # Language Specific Rules
    if is_ts:
        rules.insert(0, "**Strict Typing**: Use TypeScript interfaces where possible.")
        rules.append("**Page Object Model**: If the input looks like a Page Object, output a Class with `constructor(page: Page)`.")
    else:
        rules.insert(0, "**No Types**: Do NOT use TypeScript types (like `: Page`, `: void`). Use standard JavaScript.")
        rules.append("**Page Object Model**: If the input looks like a Page Object, output a Class with `constructor(page)`.")

    rules_text = "\n".join([f"{i+1}. {rule}" for i, rule in enumerate(rules)])

    prompt = f"""
You are an expert Test Automation Architect.
Your task is to convert Selenium Java (TestNG) code to Playwright {lang_name}.

CRITICAL: The output must be PURE Playwright. Do not retain ANY Selenium dependencies.

Rules:
{rules_text}

Input Code:
```java
{cleaned_code}
```

Output ({lang_name} Only):
"""

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        print(f"Sending request to Ollama ({model})...")
        response = requests.post(OLLAMA_URL, json=payload, timeout=120) # 2 min timeout for generation
        response.raise_for_status()
        
        data = response.json()
        raw_output = data.get("response", "")
        
        # Extract code block if present
        match = re.search(r'```typescript(.*?)```', raw_output, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        match_js = re.search(r'```javascript(.*?)```', raw_output, re.DOTALL)
        if match_js:
             return match_js.group(1).strip()

        # Fallback: Return raw output if no code block found
        return raw_output.strip()

    except requests.exceptions.RequestException as e:
        return f"// Error converting code: {str(e)}"

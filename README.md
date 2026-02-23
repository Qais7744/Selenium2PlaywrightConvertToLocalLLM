# 🚀 Selenium2Playwright Converter

**Convert Selenium Java Tests to Playwright TypeScript using Local LLM**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Playwright](https://img.shields.io/badge/Playwright-1.40%2B-orange.svg)](https://playwright.dev/python/)

An intelligent code converter that transforms Selenium Java test scripts into Playwright TypeScript code using **Local LLM** (Ollama). No API keys needed!

![Converter Interface](assets/banner.png)

---

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## ✨ Features

### 🔥 Core Features

- 🤖 **Local LLM Integration** - Uses Ollama (CodeLlama/qwen2.5-coder) - no API keys needed!
- 🔄 **Smart Conversion** - Expert LLM prompting for accurate conversions
- 📝 **Framework Support** - Handles TestNG annotations (@Test, @BeforeClass, etc.)
- ⚡ **Fast Fallback** - Pattern matching fallback when LLM is slow
- 🎯 **Zero Java Code** - Guaranteed Playwright output, no Java remnants

### 🛡️ Supported Conversions

| Selenium Java | Playwright TypeScript |
|---------------|----------------------|
| `driver.get()` | `await page.goto()` |
| `findElement(By.id)` | `page.locator("#id")` |
| `findElement(By.cssSelector)` | `page.locator("selector")` |
| `.sendKeys()` | `.fill()` |
| `.click()` | `.click()` |
| `.getText()` | `.innerText()` |
| `driver.getTitle()` | `await page.title()` |
| `@Test` | `test()` |
| `@BeforeClass` | `test.beforeAll()` |
| `Assert.assertEquals` | `expect().toBe()` |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           User Interface                │
│      (Flask Web App - Port 5000)        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│       app_llm_smart.py                  │
│  - Flask routes                         │
│  - Request handling                     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│    converter_llm_smart.py               │
│  - Expert LLM prompting                 │
│  - Pattern fallback                     │
│  - Output validation                    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Ollama (Local LLM)              │
│    - qwen2.5-coder:0.5b or similar      │
└─────────────────────────────────────────┘
```

---

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- Ollama installed locally

### Step 1: Clone the Repository

```bash
git clone https://github.com/Qais7744/Selenium2PlaywrightConvertToLocalLLM.git
cd Selenium2PlaywrightConvertToLocalLLM
```

### Step 2: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Install Ollama & Model

```bash
# Download from https://ollama.com (Windows/Mac/Linux)

# Pull a code model
ollama pull qwen2.5-coder:0.5b
```

---

## 🚀 Usage

### Start the Application

You need **TWO** terminal windows:

**Terminal 1 - Start Ollama:**
```bash
ollama serve
```

**Terminal 2 - Start Flask App:**
```bash
cd tools
python app_llm_smart.py
```

### Open Browser

Navigate to: **http://localhost:5000**

### Convert Code

1. Paste your Java Selenium code in the input area
2. Select TypeScript or JavaScript
3. Click **Convert**
4. Copy or save the converted Playwright code

---

## 📁 Project Structure

```
Selenium2PlaywrightConvertToLocalLLM/
├── README.md              # This file
├── LICENSE                # MIT License
├── requirements.txt       # Python dependencies
│
├── tools/                 # Main application
│   ├── app_llm_smart.py          # Flask web server
│   └── converter_llm_smart.py    # LLM conversion engine
│
├── templates/             # HTML templates
│   └── index.html         # Web interface
│
├── static/                # CSS/JS assets
│   └── style.css          # Styles
│
├── generated/             # Output directory
│   └── (converted files saved here)
│
└── assets/                # Images and documentation
    └── banner.png
```

---

## 🛠️ Troubleshooting

### Issue: "LLM call failed: Connection refused"

**Solution:** Ollama is not running. Start it with:
```bash
ollama serve
```

### Issue: "Read timed out"

**Solution:** The converter automatically falls back to pattern matching. No action needed!

### Issue: "ModuleNotFoundError: No module named 'flask_cors'"

**Solution:** Install dependencies:
```bash
pip install flask flask-cors requests
```

---

## 📊 Example Conversion

### Input (Java Selenium)
```java
import org.openqa.selenium.*;
import org.testng.annotations.*;

public class LoginTest {
    @Test
    public void testLogin() {
        driver.get("https://example.com");
        driver.findElement(By.id("username")).sendKeys("admin");
        driver.findElement(By.id("login-btn")).click();
        Assert.assertEquals(driver.getTitle(), "Dashboard");
    }
}
```

### Output (Playwright TypeScript)
```typescript
import { test, expect } from '@playwright/test';

test.describe('LoginTest', () => {
    test('testLogin', async ({ page }) => {
        await page.goto("https://example.com");
        await page.locator("#username").fill("admin");
        await page.locator("#login-btn").click();
        expect(await page.title()).toBe("Dashboard");
    });
});
```

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Playwright](https://playwright.dev/) - Modern web testing framework
- [Selenium](https://www.selenium.dev/) - Classic web testing framework
- [Ollama](https://ollama.com/) - Local LLM runner
- [CodeLlama](https://github.com/facebookresearch/codellama) - Code generation model

---

Made with ❤️ and 🤖 Local LLMs

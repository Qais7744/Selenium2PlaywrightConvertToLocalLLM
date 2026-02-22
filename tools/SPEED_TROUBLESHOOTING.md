# Speed Troubleshooting Guide

If conversions are still slow, follow this step-by-step guide.

## ⚡ Quick Fixes (Try These First)

### 1. Use the FAST Mode
```bash
cd tools
python app_fast.py
```

This uses a **hybrid approach**:
- 50-70% of simple conversions bypass LLM entirely (regex-only)
- Only complex code hits the LLM
- Typical speed: **0.1s - 2s** vs 10-30s

### 2. Use Smaller/Faster Model
```bash
# Pull a smaller model (if not already installed)
ollama pull qwen2.5-coder:0.5b

# Use it
export CONVERTER_MODEL=qwen2.5-coder:0.5b
python app_fast.py
```

**Model Speed Comparison:**
| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| qwen2.5-coder:0.5b | 500MB | ⚡⚡⚡ Fastest | ⭐⭐ Good |
| qwen2.5-coder:1.5b | 1.5GB | ⚡⚡ Fast | ⭐⭐⭐ Better |
| codellama:7b | 7GB | ⚡ Slow | ⭐⭐⭐⭐ Best |

### 3. Check Ollama is Running Properly
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Should return list of models
```

If Ollama is not running:
```bash
# Start Ollama
ollama serve
```

---

## 🔧 Hardware Optimizations

### Enable GPU Acceleration (if available)

**NVIDIA GPU:**
```bash
# Check if GPU is detected
ollama run qwen2.5-coder:1.5b
# Look for "CUDA" or "GPU" in startup messages
```

**CPU Only - Optimize Threads:**
```bash
# Set number of threads for Ollama
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_MAX_LOADED_MODELS=1
ollama serve
```

---

## 📊 Diagnose the Bottleneck

Run the diagnostic script:

```bash
cd tools
python diagnose_speed.py
```

This will tell you exactly where the delay is:
- **Network latency** → Check Ollama connection
- **Model loading** → Use model warming
- **Inference time** → Use smaller model
- **Pre-processing** → Code is too complex

---

## 🎯 Code-Specific Optimizations

### Split Large Files
If your code is >500 lines, split it:
```java
// Instead of one 1000-line file
// Split into: LoginTest.java, CheckoutTest.java, etc.
```

### Simplify Before Converting
Remove unnecessary code:
```java
// Remove these before converting:
- package declarations
- Standard Java imports (java.util.*)
- Comments (unless they explain logic)
- Empty lines and formatting
```

---

## 🔄 Alternative: Use Faster Backend

If Ollama is still too slow, try these alternatives:

### Option 1: LM Studio (Often Faster)
1. Download [LM Studio](https://lmstudio.ai/)
2. Load `qwen2.5-coder:0.5b` or similar
3. Start local server (default: http://localhost:1234)
4. Update config:
```python
# In converter_engine_fast.py
OLLAMA_URL = "http://localhost:1234/v1/chat/completions"
```

### Option 2: Use OpenAI API (Paid but Fast)
```python
# Update to use OpenAI instead of local LLM
import openai
# Much faster but requires API key
```

---

## 🚀 Ultimate Speed Setup

For absolute maximum speed:

```bash
# 1. Use smallest model
ollama pull qwen2.5-coder:0.5b

# 2. Run fast app
python tools/app_fast.py

# 3. In browser, use "Fast Convert" button
```

**Expected Performance:**
- Simple tests (50 lines): **0.1 - 0.5 seconds**
- Medium tests (100-200 lines): **0.5 - 2 seconds**
- Complex tests (300+ lines): **2 - 5 seconds**

---

## ❓ Still Slow?

If you've tried everything and it's still slow:

1. **Check your hardware:**
   - Minimum: 8GB RAM, modern CPU
   - Recommended: 16GB RAM, SSD, multi-core CPU

2. **Check for antivirus:**
   - Some antivirus software scans every HTTP request
   - Add Ollama to whitelist

3. **Try cloud alternative:**
   - GitHub Copilot
   - ChatGPT/CodeGPT
   - Claude

---

## 📞 Debug Output

Run with debug logging:
```bash
# Windows PowerShell
$env:DEBUG="1"
python tools/app_fast.py

# You'll see timing for each step:
# [DEBUG] Pre-processing: 12ms
# [DEBUG] Cache check: 1ms
# [DEBUG] Regex conversion: 45ms
# [DEBUG] Total: 58ms
```

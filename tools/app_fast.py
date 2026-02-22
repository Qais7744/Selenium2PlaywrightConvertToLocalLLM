"""
Ultra-Fast Flask App for Selenium2Playwright

This is the FASTEST version using:
- Hybrid regex+LLM approach (50-70% bypass LLM entirely)
- Model warming to eliminate cold-start
- Minimal prompts for faster inference
- No streaming overhead
- In-memory caching

Usage:
    python app_fast.py
    
This version prioritizes speed over perfect accuracy.
For production use, use app_optimized.py instead.
"""

import os
import sys
import time
import asyncio
import traceback
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from converter_engine_fast import FastConverter, get_converter, convert_code
    print("✅ Loaded fast converter engine")
except Exception as e:
    print(f"❌ Error loading converter: {e}")
    traceback.print_exc()
    sys.exit(1)

# Flask app
app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

# Ensure directories
GENERATED_DIR = os.path.join(os.path.dirname(__file__), '../generated')
os.makedirs(GENERATED_DIR, exist_ok=True)

# Initialize converter on startup
print("🚀 Initializing FAST converter...")
try:
    converter = get_converter()
    print("✅ Converter ready")
except Exception as e:
    print(f"❌ Failed to initialize converter: {e}")
    traceback.print_exc()
    sys.exit(1)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "converter": "fast",
        "model": converter.client.model
    })


@app.route('/convert', methods=['POST'])
def convert():
    """Ultra-fast conversion endpoint."""
    data = request.get_json() or {}
    java_code = data.get('source_code', '')
    language = data.get('language', 'typescript')
    
    print(f"\n📝 Conversion request received")
    print(f"   Language: {language}")
    print(f"   Code length: {len(java_code)} chars")
    
    if not java_code:
        print("   ❌ Error: No source code provided")
        return jsonify({"status": "error", "message": "No source code"}), 400
    
    try:
        start = time.time()
        result = convert_code(java_code, language)
        elapsed = time.time() - start
        
        print(f"   ✅ Conversion complete in {elapsed:.3f}s")
        
        if result.startswith("// Error"):
            print(f"   ❌ Conversion error: {result}")
            return jsonify({
                "status": "error",
                "message": result.replace("// Error: ", "")
            }), 500
        
        return jsonify({
            "status": "success",
            "converted_code": result,
            "converter": "fast",
            "time": round(elapsed, 3)
        })
        
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/convert/detailed', methods=['POST'])
def convert_detailed():
    """Conversion with full details."""
    data = request.get_json() or {}
    java_code = data.get('source_code', '')
    language = data.get('language', 'typescript')
    
    if not java_code:
        return jsonify({"status": "error", "message": "No source code"}), 400
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(converter.convert(java_code, language))
        loop.close()
        
        if result['status'] == 'error':
            return jsonify(result), 500
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Exception in convert_detailed: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/stats')
def stats():
    """Get converter statistics."""
    return jsonify(converter.get_stats())


@app.route('/save', methods=['POST'])
def save():
    """Save converted code."""
    data = request.get_json() or {}
    ts_code = data.get('converted_code', '')
    filename = data.get('filename', 'converted_test.spec.ts')
    
    if not ts_code:
        return jsonify({"status": "error", "message": "No code"}), 400
    
    filename = os.path.basename(filename)
    if '..' in filename:
        return jsonify({"status": "error", "message": "Invalid filename"}), 400
    
    try:
        file_path = os.path.join(GENERATED_DIR, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(ts_code)
        print(f"💾 Saved to: {file_path}")
        return jsonify({"status": "success", "file_path": file_path})
    except Exception as e:
        print(f"❌ Save error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════╗
║     SELENIUM2PLAYWRIGHT - ULTRA FAST MODE ⚡              ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  🚀 Speed optimizations:                                  ║
║     • 50-70% conversions bypass LLM (regex-only)          ║
║     • Model warming eliminates cold-start                 ║
║     • Minimal prompts for faster inference                ║
║     • No streaming overhead                               ║
║                                                           ║
║  ⚠️  Trade-off:                                           ║
║     • Speed > Perfect accuracy                            ║
║     • Complex code may need manual review                 ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
""")
    print("📡 Server: http://localhost:5000")
    print("📊 Stats:  http://localhost:5000/stats")
    print("🏥 Health: http://localhost:5000/health")
    print()
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True, use_reloader=False)

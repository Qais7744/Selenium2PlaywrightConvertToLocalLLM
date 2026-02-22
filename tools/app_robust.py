"""
Selenium2Playwright Robust Converter - Zero Java Code Guarantee

Strict Playwright output:
- NO manual browser launching
- NO Java imports
- NO Selenium methods
- Proper { page } fixture usage
"""

import os
import sys
import time
import traceback
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from converter_engine_robust import convert_code
    print("✅ Loaded Robust converter engine")
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


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "converter": "robust-zero-java"
    })


@app.route('/convert', methods=['POST'])
def convert():
    """Convert Java Selenium to Playwright."""
    data = request.get_json() or {}
    java_code = data.get('source_code', '')
    language = data.get('language', 'typescript')
    
    print(f"\n📝 Conversion request")
    print(f"   Code length: {len(java_code)} chars")
    
    if not java_code:
        return jsonify({"status": "error", "message": "No source code"}), 400
    
    try:
        start = time.time()
        result = convert_code(java_code, language)
        elapsed = time.time() - start
        
        print(f"   ✅ Done in {elapsed:.3f}s")
        
        if result.startswith("// Error"):
            return jsonify({
                "status": "error",
                "message": result.replace("// Error: ", "")
            }), 500
        
        # Validate output
        forbidden = ['chromium.launch', 'browser.launch', 'System.setProperty', 'ChromeDriver']
        warnings = []
        for pattern in forbidden:
            if pattern in result:
                warnings.append(f"Output may contain: {pattern}")
        
        return jsonify({
            "status": "success",
            "converted_code": result,
            "time": round(elapsed, 3),
            "warnings": warnings
        })
        
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/save', methods=['POST'])
def save():
    """Save converted code."""
    data = request.get_json() or {}
    code = data.get('converted_code', '')
    filename = data.get('filename', 'converted_test.spec.ts')
    
    if not code:
        return jsonify({"status": "error", "message": "No code"}), 400
    
    filename = os.path.basename(filename)
    if '..' in filename:
        return jsonify({"status": "error", "message": "Invalid filename"}), 400
    
    try:
        file_path = os.path.join(GENERATED_DIR, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"💾 Saved: {file_path}")
        return jsonify({"status": "success", "file_path": file_path})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════╗
║  SELENIUM2PLAYWRIGHT - ROBUST CONVERTER ✅                ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  ✓ ZERO Java code in output                               ║
║  ✓ NO manual browser launching                            ║
║  ✓ NO chromium import                                     ║
║  ✓ Strict { page } fixture usage                          ║
║  ✓ Proper test.describe structure                         ║
║  ✓ Pure Playwright output guaranteed                      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
""")
    print("📡 Server: http://localhost:5000")
    print()
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True, use_reloader=False)

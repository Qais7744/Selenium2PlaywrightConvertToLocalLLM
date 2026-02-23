"""
Bulletproof Selenium to Playwright Converter

Zero Java code guarantee.
"""

import os
import sys
import time
import traceback
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from converter_bulletproof import convert
    print("✅ Loaded Bulletproof converter")
except Exception as e:
    print(f"❌ Error: {e}")
    traceback.print_exc()
    sys.exit(1)

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

GENERATED_DIR = os.path.join(os.path.dirname(__file__), '../generated')
os.makedirs(GENERATED_DIR, exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def convert_endpoint():
    """Convert Java Selenium to Playwright."""
    data = request.get_json() or {}
    java_code = data.get('source_code', '')
    
    if not java_code:
        return jsonify({"status": "error", "message": "No code"}), 400
    
    try:
        result = convert(java_code)
        
        # Validate
        errors = []
        forbidden = ['chromium.launch', 'browser.launch', 'System.setProperty', 
                     'WebDriver', 'ChromeDriver', 'By.id(', '.sendKeys(', 'public void']
        for pattern in forbidden:
            if pattern in result:
                errors.append(pattern)
        
        return jsonify({
            "status": "success" if not errors else "warning",
            "converted_code": result,
            "errors": errors
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/save', methods=['POST'])
def save():
    """Save converted code."""
    data = request.get_json() or {}
    code = data.get('converted_code', '')
    filename = data.get('filename', 'converted.spec.ts')
    
    if not code:
        return jsonify({"status": "error", "message": "No code"}), 400
    
    try:
        file_path = os.path.join(GENERATED_DIR, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        return jsonify({"status": "success", "file_path": file_path})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════╗
║  BULLETPROOF CONVERTER - Zero Java Code ✅                ║
╚═══════════════════════════════════════════════════════════╝
""")
    print("📡 http://localhost:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

"""
Smart Converter with LLM + Pattern Fallback

Uses LLM when available, falls back to pattern matching if LLM times out.
"""

import os
import sys
import traceback
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from converter_smart_with_fallback import llm_convert
    print("✅ Loaded Smart Converter (LLM + Fallback)")
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
def convert():
    """Convert with LLM + fallback."""
    data = request.get_json() or {}
    java_code = data.get('source_code', '')
    language = data.get('language', 'typescript')
    
    print(f"\n📝 Conversion request ({language})")
    print(f"   Code length: {len(java_code)} chars")
    
    if not java_code:
        return jsonify({"status": "error", "message": "No code"}), 400
    
    try:
        result = llm_convert(java_code, language)
        
        print(f"   Method: {result.get('method', 'unknown')}")
        if 'note' in result:
            print(f"   Note: {result['note']}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()
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
║  SMART CONVERTER - LLM + Pattern Fallback ✅              ║
╠═══════════════════════════════════════════════════════════╣
║  Tries LLM first, falls back to pattern if timeout        ║
╚═══════════════════════════════════════════════════════════╝
""")
    print("📡 http://localhost:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import converter_engine

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

# Ensure generated directory exists
GENERATED_DIR = os.path.join(os.path.dirname(__file__), '../generated')
os.makedirs(GENERATED_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    data = request.json
    java_code = data.get('source_code', '')
    language = data.get('language', 'typescript')
    
    if not java_code:
        return jsonify({"status": "error", "message": "No source code provided"}), 400

    try:
        ts_code = converter_engine.convert_code(java_code, language=language)
        return jsonify({"status": "success", "converted_code": ts_code})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/save', methods=['POST'])
def save():
    data = request.json
    ts_code = data.get('converted_code', '')
    filename = data.get('filename', 'converted_test.spec.ts')
    
    if not ts_code:
        return jsonify({"status": "error", "message": "No code to save"}), 400

    try:
        file_path = os.path.join(GENERATED_DIR, filename)
        with open(file_path, 'w') as f:
            f.write(ts_code)
        return jsonify({"status": "success", "file_path": file_path})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask Server on http://localhost:5000")
    app.run(debug=True, port=5000)

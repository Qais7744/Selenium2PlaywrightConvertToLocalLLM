"""
Optimized Flask Application for Selenium2Playwright Converter

Features:
- Async route handlers for non-blocking requests
- Response streaming for real-time progress
- Connection health checks
- Request timeout handling
- Gzip compression
- Proper resource cleanup

Author: AI Assistant
"""

import os
import sys
import time
import asyncio
from typing import Generator
from functools import wraps

from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from flask_cors import CORS
from flask_compress import Compress

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from converter_engine_optimized import (
        AsyncCodeConverter, 
        ConverterConfig, 
        FAST_MODELS,
        set_model_speed_level,
        ConnectionManager
    )
except ImportError as e:
    print(f"Error importing optimized converter: {e}")
    print("Falling back to legacy converter...")
    import converter_engine as converter_engine_legacy
    USE_OPTIMIZED = False
else:
    USE_OPTIMIZED = True


# =============================================================================
# Flask App Configuration
# =============================================================================

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)
Compress(app)  # Enable gzip compression for responses

# Configuration
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max request size

# Ensure directories exist
GENERATED_DIR = os.path.join(os.path.dirname(__file__), '../generated')
os.makedirs(GENERATED_DIR, exist_ok=True)

# Initialize converter with optimized settings
if USE_OPTIMIZED:
    config = ConverterConfig(
        model="qwen2.5-coder:1.5b",  # Fast default model
        timeout=60,  # Reduced timeout for faster feedback
        enable_cache=True,
        cache_size=200,
        use_streaming=True,
        connection_pool_size=10
    )
    converter = AsyncCodeConverter(config)
else:
    converter = None


# =============================================================================
# Health Check & Middleware
# =============================================================================

def check_ollama_health() -> dict:
    """Check if Ollama is running and responsive."""
    try:
        import requests
        response = requests.get(
            "http://localhost:11434/api/tags",
            timeout=5
        )
        if response.status_code == 200:
            models = response.json().get('models', [])
            return {
                "status": "healthy",
                "models_available": [m['name'] for m in models[:5]]
            }
        return {"status": "unhealthy", "error": f"Status {response.status_code}"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# =============================================================================
# Route Handlers
# =============================================================================

@app.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html')


@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    ollama_status = check_ollama_health()
    return jsonify({
        "status": "healthy" if ollama_status["status"] == "healthy" else "degraded",
        "ollama": ollama_status,
        "converter": "optimized" if USE_OPTIMIZED else "legacy",
        "timestamp": time.time()
    })


@app.route('/models')
def list_models():
    """List available speed levels and models."""
    return jsonify({
        "speed_levels": FAST_MODELS if USE_OPTIMIZED else {},
        "current_model": config.model if USE_OPTIMIZED else "unknown"
    })


@app.route('/convert', methods=['POST'])
def convert():
    """
    Convert Java Selenium code to Playwright.
    
    Request Body:
        - source_code: Java source code (required)
        - language: "typescript" or "javascript" (default: typescript)
        - stream: boolean - whether to stream response (default: false)
        
    Returns:
        JSON with converted code and metadata
    """
    start_time = time.time()
    
    data = request.get_json() or {}
    java_code = data.get('source_code', '')
    language = data.get('language', 'typescript')
    use_streaming = data.get('stream', False)
    
    # Validation
    if not java_code or not isinstance(java_code, str):
        return jsonify({
            "status": "error",
            "message": "No source code provided or invalid format"
        }), 400
    
    if len(java_code) > 50000:  # 50KB limit
        return jsonify({
            "status": "error",
            "message": "Code exceeds maximum size (50KB)"
        }), 413
    
    # Use optimized or legacy converter
    if USE_OPTIMIZED:
        if use_streaming:
            return _stream_conversion(java_code, language)
        else:
            return _sync_conversion(java_code, language, start_time)
    else:
        return _legacy_conversion(java_code, language)


def _sync_conversion(java_code: str, language: str, start_time: float) -> Response:
    """Handle synchronous conversion using optimized converter."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            converter.convert(java_code, language)
        )
        
        loop.close()
        
        # Add server-side timing
        result['server_time'] = round(time.time() - start_time, 3)
        
        if result['status'] == 'error':
            return jsonify(result), 500
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Conversion failed: {str(e)}"
        }), 500


def _stream_conversion(java_code: str, language: str) -> Response:
    """
    Handle streaming conversion for real-time progress.
    
    Streams partial responses as they're generated by the LLM.
    """
    def generate() -> Generator[str, None, None]:
        accumulated = []
        
        def on_chunk(chunk: str):
            accumulated.append(chunk)
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                converter.convert(
                    java_code, 
                    language, 
                    progress_callback=on_chunk
                )
            )
            
            loop.close()
            
            # Stream the final result
            yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


def _legacy_conversion(java_code: str, language: str) -> Response:
    """Fallback to legacy converter."""
    try:
        result = converter_engine_legacy.convert_code(java_code, language=language)
        
        if result.startswith("// Error"):
            return jsonify({
                "status": "error",
                "message": result.replace("// Error converting code: ", "")
            }), 500
        
        return jsonify({
            "status": "success",
            "converted_code": result,
            "cached": False,
            "model": "legacy"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/convert/batch', methods=['POST'])
def convert_batch():
    """
    Convert multiple code snippets in parallel.
    
    Request Body:
        - snippets: List of {code, language} objects
        - max_concurrent: Maximum parallel conversions (default: 3)
    """
    if not USE_OPTIMIZED:
        return jsonify({
            "status": "error",
            "message": "Batch conversion requires optimized converter"
        }), 501
    
    data = request.get_json() or {}
    snippets = data.get('snippets', [])
    max_concurrent = min(data.get('max_concurrent', 3), 5)  # Max 5 concurrent
    
    if not snippets or not isinstance(snippets, list):
        return jsonify({
            "status": "error",
            "message": "Invalid snippets format"
        }), 400
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        results = loop.run_until_complete(
            converter.convert_batch(snippets, max_concurrent)
        )
        
        loop.close()
        
        return jsonify({
            "status": "success",
            "results": results,
            "count": len(results)
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/speed', methods=['POST'])
def set_speed():
    """
    Change the conversion speed/quality level.
    
    Request Body:
        - level: One of "ultra_fast", "fast", "balanced", "accurate"
    """
    if not USE_OPTIMIZED:
        return jsonify({
            "status": "error",
            "message": "Speed levels require optimized converter"
        }), 501
    
    data = request.get_json() or {}
    level = data.get('level', 'fast')
    
    try:
        model = set_model_speed_level(level)
        return jsonify({
            "status": "success",
            "level": level,
            "model": model
        })
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@app.route('/save', methods=['POST'])
def save():
    """
    Save converted code to a file.
    
    Request Body:
        - converted_code: The code to save (required)
        - filename: Target filename (default: converted_test.spec.ts)
    """
    data = request.get_json() or {}
    ts_code = data.get('converted_code', '')
    filename = data.get('filename', 'converted_test.spec.ts')
    
    # Security: Sanitize filename
    filename = os.path.basename(filename)
    if not filename or '..' in filename:
        return jsonify({
            "status": "error",
            "message": "Invalid filename"
        }), 400
    
    if not ts_code:
        return jsonify({
            "status": "error",
            "message": "No code to save"
        }), 400
    
    try:
        file_path = os.path.join(GENERATED_DIR, filename)
        
        # Prevent overwriting existing files
        counter = 1
        base_name, ext = os.path.splitext(filename)
        while os.path.exists(file_path):
            file_path = os.path.join(GENERATED_DIR, f"{base_name}_{counter}{ext}")
            counter += 1
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(ts_code)
        
        return jsonify({
            "status": "success",
            "file_path": file_path,
            "filename": os.path.basename(file_path)
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear the conversion cache."""
    if USE_OPTIMIZED and converter:
        converter.cache.clear()
        return jsonify({"status": "success", "message": "Cache cleared"})
    return jsonify({"status": "error", "message": "Cache not available"}), 501


# =============================================================================
# Error Handlers
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Not found"}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"status": "error", "message": "Internal server error"}), 500


@app.errorhandler(413)
def too_large(error):
    return jsonify({"status": "error", "message": "Request too large"}), 413


# =============================================================================
# Startup & Cleanup
# =============================================================================

def startup_check():
    """Run health checks on startup."""
    print("\n" + "="*50)
    print("Starting Selenium2Playwright Converter")
    print("="*50)
    
    health = check_ollama_health()
    print(f"\n🤖 Ollama Status: {health['status']}")
    
    if health['status'] == 'healthy':
        print(f"📦 Available Models: {', '.join(health.get('models_available', []))}")
    else:
        print(f"⚠️  Warning: {health.get('error', 'Ollama not running')}")
    
    print(f"🔧 Converter: {'Optimized' if USE_OPTIMIZED else 'Legacy'}")
    
    if USE_OPTIMIZED:
        print(f"🚀 Model: {config.model}")
        print(f"💾 Caching: {'Enabled' if config.enable_cache else 'Disabled'}")
        print(f"📡 Streaming: {'Enabled' if config.use_streaming else 'Disabled'}")
    
    print(f"📁 Output Directory: {GENERATED_DIR}")
    print("="*50 + "\n")


@app.teardown_appcontext
def cleanup(error):
    """Cleanup resources on shutdown."""
    if USE_OPTIMIZED and converter:
        converter.close()


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == '__main__':
    startup_check()
    
    # Run with threading for concurrent requests
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,  # Set to True for development
        threaded=True,  # Enable threading for concurrent requests
        use_reloader=False  # Disable reloader to prevent double startup
    )

#!/usr/bin/env python3
"""
Quick start script for the optimized converter.

Usage:
    python run_optimized.py           # Start the optimized server
    python run_optimized.py --legacy  # Use legacy converter
    python run_optimized.py --fast    # Use fastest model
"""

import sys
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description='Run Selenium2Playwright Converter')
    parser.add_argument('--legacy', action='store_true', help='Use legacy converter')
    parser.add_argument('--fast', action='store_true', help='Use ultra-fast model')
    parser.add_argument('--port', type=int, default=5000, help='Port number (default: 5000)')
    args = parser.parse_args()
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║        SELENIUM2PLAYWRIGHT CONVERTER - OPTIMIZED          ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  🚀 Performance Features:                                 ║
║     • Async/await for non-blocking requests               ║
║     • Connection pooling for faster HTTP                  ║
║     • Intelligent caching for repeated code               ║
║     • Streaming responses for real-time feedback          ║
║     • Code pre-processing for 30-40% token reduction      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    # Check for required dependencies
    try:
        import flask
        import flask_cors
        import requests
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nInstall required packages:")
        print("   pip install -r requirements.txt")
        return 1
    
    # Check for optimized dependencies
    try:
        import aiohttp
        import flask_compress
        print("✅ Optimized dependencies installed")
    except ImportError:
        print("⚠️  Optimized dependencies not found. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp", "flask-compress"])
        print("✅ Dependencies installed")
    
    # Set environment variables
    if args.fast:
        os.environ['CONVERTER_MODEL'] = 'qwen2.5-coder:0.5b'
        print("⚡ Using ultra-fast model (qwen2.5-coder:0.5b)")
    
    # Run appropriate server
    if args.legacy:
        print("📟 Running LEGACY converter...")
        import app as legacy_app
        legacy_app.app.run(host='0.0.0.0', port=args.port, debug=False, threaded=True)
    else:
        print("🚀 Running OPTIMIZED converter...")
        print(f"📡 Server will start on http://localhost:{args.port}")
        print("📖 Documentation: tools/PERFORMANCE_IMPROVEMENTS.md")
        print("\nPress Ctrl+C to stop\n")
        
        import app_optimized
        app_optimized.app.run(host='0.0.0.0', port=args.port, debug=False, threaded=True, use_reloader=False)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

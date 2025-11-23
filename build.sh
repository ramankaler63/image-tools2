#!/usr/bin/env bash
# build.sh - Custom build script for Render

set -o errexit

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🤖 Pre-downloading rembg AI model..."
python - <<EOF
try:
    from rembg import new_session
    print("Initializing rembg session...")
    session = new_session("u2net")
    print("✅ Model downloaded successfully!")
except Exception as e:
    print(f"⚠️ Warning: Could not pre-download model: {e}")
    print("Model will be downloaded on first use")
EOF

echo "✅ Build complete!"
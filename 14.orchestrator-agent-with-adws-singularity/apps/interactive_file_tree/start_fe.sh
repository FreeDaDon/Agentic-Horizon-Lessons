#!/bin/bash
# Interactive File Tree Frontend Startup Script
# Runs the Vue 3 + Vite development server on port 5180

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="${SCRIPT_DIR}/frontend"

echo "=========================================="
echo "Interactive File Tree - Frontend"
echo "=========================================="
echo ""

# Check if we're in the frontend directory
if [ ! -f "${FRONTEND_DIR}/package.json" ]; then
    echo "Error: package.json not found in ${FRONTEND_DIR}"
    exit 1
fi

cd "${FRONTEND_DIR}"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
    echo ""
fi

echo "Starting development server on port 5180..."
echo "Open http://localhost:5180 in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm run dev

#!/bin/bash
# Healthcare Recovery Forecast Frontend - Quick Start Script
# This script sets up and runs the frontend in one command

set -e

echo "🏥 Healthcare Recovery Forecast - Frontend Setup"
echo "=================================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    echo "   Download from: https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js $(node --version) found"
echo ""

# Navigate to frontend directory
cd frontend

echo "📦 Installing dependencies..."
npm install

echo ""
echo "✅ Dependencies installed"
echo ""

# Create .env.local if it doesn't exist
if [ ! -f .env.local ]; then
    echo "🔧 Creating .env.local..."
    cp .env.example .env.local
    echo "✅ .env.local created"
    echo ""
fi

# Start dev server
echo "🚀 Starting development server..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Frontend running at: http://localhost:3000"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Demo Login Credentials:"
echo "   Hospital ID: any_text"
echo "   Password: any_text"
echo ""
echo "📚 Documentation:"
echo "   - README.md - Feature overview"
echo "   - SETUP_GUIDE.md - Configuration & customization"
echo "   - INTEGRATION_GUIDE.md - Backend integration"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm run dev

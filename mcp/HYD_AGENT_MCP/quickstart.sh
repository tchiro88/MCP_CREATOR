#!/bin/bash

# Hydraulic Analysis MCP Server - Quick Start Script
# This script helps you get up and running quickly

set -e

echo "=================================================="
echo "Hydraulic Analysis MCP Server - Quick Start"
echo "=================================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✓ Docker is installed"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    echo "Please install Docker Compose from: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker Compose is installed"

# Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: You must edit .env and add your API key!"
    echo "   Run: nano .env"
    echo "   Add your OPENAI_API_KEY or OPENROUTER_API_KEY"
    echo ""
    read -p "Press Enter once you've added your API key..."
fi

# Validate API key is set
if ! grep -q "^OPENAI_API_KEY=sk-" .env && ! grep -q "^OPENROUTER_API_KEY=sk-" .env; then
    echo ""
    echo "⚠️  Warning: No API key found in .env file"
    echo "Please add your OPENAI_API_KEY or OPENROUTER_API_KEY to .env"
    echo ""
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create necessary directories
echo ""
echo "📁 Creating directories..."
mkdir -p schematics manufacturer_docs machines database
echo "✓ Directories created"

# Build Docker image
echo ""
echo "🐳 Building Docker image..."
docker-compose build

echo ""
echo "✓ Docker image built successfully"

# Test the server
echo ""
echo "🧪 Testing server..."
if docker-compose run --rm hydraulic-mcp-server python -c "from config import config; valid, err = config.validate(); print('✓ Configuration valid' if valid else f'❌ Error: {err}'); exit(0 if valid else 1)"; then
    echo "✓ Server configuration is valid"
else
    echo "❌ Server configuration failed"
    exit 1
fi

# Get absolute path
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo ""
echo "=================================================="
echo "✅ Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Add schematics to: $SCRIPT_DIR/schematics/"
echo "2. Add manufacturer docs to: $SCRIPT_DIR/manufacturer_docs/"
echo ""
echo "3. Configure your MCP client:"
echo ""
echo "   For Claude Desktop, add to claude_desktop_config.json:"
echo "   (Location: ~/Library/Application Support/Claude/claude_desktop_config.json on macOS)"
echo ""
echo '   {'
echo '     "mcpServers": {'
echo '       "hydraulic-analysis": {'
echo '         "command": "docker",'
echo '         "args": ['
echo '           "run", "-i", "--rm",'
echo "           \"-v\", \"$SCRIPT_DIR/schematics:/app/schematics\","
echo "           \"-v\", \"$SCRIPT_DIR/manufacturer_docs:/app/manufacturer_docs\","
echo "           \"-v\", \"$SCRIPT_DIR/machines:/app/machines\","
echo "           \"-v\", \"$SCRIPT_DIR/database:/app/database\","
echo '           "-e", "OPENAI_API_KEY=your-api-key-here",'
echo '           "hydraulic-mcp-server"'
echo '         ]'
echo '       }'
echo '     }'
echo '   }'
echo ""
echo "4. Restart Claude Desktop or Cursor"
echo ""
echo "5. Try asking:"
echo '   "List available schematics"'
echo '   "Analyze schematics/my_schematic.png for Machine A"'
echo ""
echo "For detailed instructions, see:"
echo "  - SETUP.md (installation guide)"
echo "  - USAGE.md (usage examples)"
echo "  - README.md (overview)"
echo ""
echo "=================================================="

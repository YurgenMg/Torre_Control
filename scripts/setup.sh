#!/bin/bash
# ============================================================================
# TORRE CONTROL - Setup Script
# Automatiza el setup inicial del ambiente de desarrollo
# ============================================================================

set -e  # Exit on any error

echo "🚀 TORRE CONTROL - Environment Setup"
echo "===================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
echo "🔍 Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker Desktop.${NC}"
    exit 1
fi

if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker daemon is not running. Please start Docker Desktop.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Start containers
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for Postgres to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Check PostgreSQL connection
echo "🔌 Testing PostgreSQL connection..."
if docker exec supply_chain_db pg_isready -U admin > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
else
    echo -e "${RED}❌ PostgreSQL is not responding${NC}"
    exit 1
fi
echo ""

# Create schema and tables
echo "📊 Creating database schema..."
docker exec supply_chain_db psql -U admin -d supply_chain_dw -f /sql/ddl/01_schema_base.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Schema created successfully${NC}"
else
    echo -e "${RED}❌ Failed to create schema${NC}"
    exit 1
fi
echo ""

# Show connection info
echo "📋 Connection Information:"
echo "=========================="
echo "Host: localhost"
echo "Port: 5432"
echo "Database: supply_chain_dw"
echo "Username: admin"
echo "Password: adminpassword"
echo ""

# Show next steps
echo "🎯 Next Steps:"
echo "=============="
echo "1. Open VS Code"
echo "2. Install SQLTools extension (if not already installed)"
echo "3. Use the connection profile 'Torre Control - Local Dev'"
echo "4. Open PgAdmin at http://localhost:5050"
echo "   - Email: admin@dataco.com"
echo "   - Password: adminpassword"
echo ""

echo -e "${GREEN}✅ Setup completed successfully!${NC}"

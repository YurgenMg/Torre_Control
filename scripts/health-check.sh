#!/bin/bash
# ============================================================================
# TORRE CONTROL - Health Check Script
# Verifica que todo esté funcionando correctamente
# ============================================================================

echo "🏥 TORRE CONTROL - Health Check"
echo "================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Docker
echo "1️⃣  Docker Status"
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker is running${NC}"
else
    echo -e "${RED}❌ Docker is NOT running${NC}"
fi
echo ""

# Check containers
echo "2️⃣  Containers Status"
if docker ps | grep -q supply_chain_db; then
    echo -e "${GREEN}✅ PostgreSQL container is running${NC}"
else
    echo -e "${RED}❌ PostgreSQL container is NOT running${NC}"
fi

if docker ps | grep -q pgadmin_supply_chain; then
    echo -e "${GREEN}✅ PgAdmin container is running${NC}"
else
    echo -e "${YELLOW}⚠️  PgAdmin container is NOT running${NC}"
fi
echo ""

# Check database connection
echo "3️⃣  Database Connection"
if docker exec supply_chain_db pg_isready -U admin > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL is responding${NC}"
    
    # Check if schema exists
    SCHEMA_CHECK=$(docker exec supply_chain_db psql -U admin -d supply_chain_dw -t -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'dw';" 2>/dev/null | grep -c "dw")
    
    if [ "$SCHEMA_CHECK" -gt 0 ]; then
        echo -e "${GREEN}✅ DW schema exists${NC}"
        
        # Count tables
        TABLE_COUNT=$(docker exec supply_chain_db psql -U admin -d supply_chain_dw -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='dw';" 2>/dev/null | tr -d ' ')
        echo -e "${GREEN}✅ Tables in DW schema: $TABLE_COUNT${NC}"
    else
        echo -e "${YELLOW}⚠️  DW schema does NOT exist. Run 'scripts/setup.sh'${NC}"
    fi
else
    echo -e "${RED}❌ PostgreSQL is NOT responding${NC}"
fi
echo ""

# Check SQL files
echo "4️⃣  SQL Files"
if [ -f "sql/ddl/01_schema_base.sql" ]; then
    echo -e "${GREEN}✅ DDL schema file exists${NC}"
else
    echo -e "${RED}❌ DDL schema file NOT found${NC}"
fi

if [ -f "sql/queries/q1_q5_strategic_questions.sql" ]; then
    echo -e "${GREEN}✅ Query file exists${NC}"
else
    echo -e "${RED}❌ Query file NOT found${NC}"
fi
echo ""

# Check project structure
echo "5️⃣  Project Structure"
DIRS=("data/raw" "data/processed" "sql/ddl" "sql/queries" "scripts" ".vscode")
for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✅ $dir exists${NC}"
    else
        echo -e "${RED}❌ $dir does NOT exist${NC}"
    fi
done
echo ""

# Access information
echo "6️⃣  Access Information"
echo "========================"
echo "VS Code SQLTools:"
echo "  Connection: Torre Control - Local Dev"
echo "  Host: localhost:5432"
echo ""
echo "PgAdmin:"
echo "  URL: http://localhost:5050"
echo "  Email: admin@dataco.com"
echo "  Password: adminpassword"
echo ""

echo -e "${GREEN}✅ Health check completed!${NC}"

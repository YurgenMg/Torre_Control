# =============================================================================
# TORRE CONTROL - Health Check Script (PowerShell for Windows)
# Verifica que todo esté funcionando correctamente
# =============================================================================

Write-Host "🏥 TORRE CONTROL - Health Check`n" -ForegroundColor Cyan

# Check Docker
Write-Host "1️⃣  Docker Status"
try {
    docker info > $null 2>&1
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is NOT running" -ForegroundColor Red
}
Write-Host ""

# Check containers
Write-Host "2️⃣  Containers Status"
$postgres_running = docker ps | Select-String "supply_chain_db"
if ($postgres_running) {
    Write-Host "✅ PostgreSQL container is running" -ForegroundColor Green
} else {
    Write-Host "❌ PostgreSQL container is NOT running" -ForegroundColor Red
}

$pgadmin_running = docker ps | Select-String "pgadmin_supply_chain"
if ($pgadmin_running) {
    Write-Host "✅ PgAdmin container is running" -ForegroundColor Green
} else {
    Write-Host "⚠️  PgAdmin container is NOT running" -ForegroundColor Yellow
}
Write-Host ""

# Check database connection
Write-Host "3️⃣  Database Connection"
try {
    docker exec supply_chain_db pg_isready -U admin > $null 2>&1
    Write-Host "✅ PostgreSQL is responding" -ForegroundColor Green
    
    # Check if schema exists
    $schema_check = docker exec supply_chain_db psql -U admin -d supply_chain_dw -t -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'dw';" 2>$null
    
    if ($schema_check -contains "dw") {
        Write-Host "✅ DW schema exists" -ForegroundColor Green
        
        # Count tables
        $table_count = docker exec supply_chain_db psql -U admin -d supply_chain_dw -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='dw';" 2>$null
        Write-Host "✅ Tables in DW schema: $table_count" -ForegroundColor Green
    } else {
        Write-Host "⚠️  DW schema does NOT exist. Run 'scripts/setup.ps1'" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ PostgreSQL is NOT responding" -ForegroundColor Red
}
Write-Host ""

# Check SQL files
Write-Host "4️⃣  SQL Files"
if (Test-Path "sql/ddl/01_schema_base.sql") {
    Write-Host "✅ DDL schema file exists" -ForegroundColor Green
} else {
    Write-Host "❌ DDL schema file NOT found" -ForegroundColor Red
}

if (Test-Path "sql/queries/q1_q5_strategic_questions.sql") {
    Write-Host "✅ Query file exists" -ForegroundColor Green
} else {
    Write-Host "❌ Query file NOT found" -ForegroundColor Red
}
Write-Host ""

# Check project structure
Write-Host "5️⃣  Project Structure"
$dirs = @("data/raw", "data/processed", "sql/ddl", "sql/queries", "scripts", ".vscode")
foreach ($dir in $dirs) {
    if (Test-Path $dir) {
        Write-Host "✅ $dir exists" -ForegroundColor Green
    } else {
        Write-Host "❌ $dir does NOT exist" -ForegroundColor Red
    }
}
Write-Host ""

# Access information
Write-Host "6️⃣  Access Information" -ForegroundColor Cyan
Write-Host "========================"
Write-Host "VS Code SQLTools:"
Write-Host "  Connection: Torre Control - Local Dev"
Write-Host "  Host: localhost:5432`n"

Write-Host "PgAdmin:"
Write-Host "  URL: http://localhost:5050"
Write-Host "  Email: admin@dataco.com"
Write-Host "  Password: adminpassword`n"

Write-Host "✅ Health check completed!" -ForegroundColor Green

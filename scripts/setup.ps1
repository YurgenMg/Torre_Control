# =============================================================================
# TORRE CONTROL - Setup Script (PowerShell for Windows)
# Automatiza el setup inicial del ambiente de desarrollo
# =============================================================================

Write-Host "🚀 TORRE CONTROL - Environment Setup (Windows)" -ForegroundColor Cyan
Write-Host "=============================================`n"

# Check if Docker is running
Write-Host "🔍 Checking Docker..." -ForegroundColor Yellow
try {
    docker info > $null 2>&1
    Write-Host "✅ Docker is running`n" -ForegroundColor Green
}
catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop.`n" -ForegroundColor Red
    exit 1
}

# Start containers
Write-Host "🐳 Starting Docker containers..." -ForegroundColor Yellow
docker-compose up -d

# Wait for Postgres to be ready
Write-Host "⏳ Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check PostgreSQL connection
Write-Host "🔌 Testing PostgreSQL connection..." -ForegroundColor Yellow
docker exec supply_chain_db pg_isready -U admin 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PostgreSQL is ready`n" -ForegroundColor Green
}
else {
    Write-Host "❌ PostgreSQL is not responding`n" -ForegroundColor Red
    exit 1
}

# Create schema and tables
Write-Host "📊 Creating database schema..." -ForegroundColor Yellow
docker exec supply_chain_db psql -U admin -d supply_chain_dw -f /sql/ddl/01_schema_base.sql

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Schema created successfully`n" -ForegroundColor Green
}
else {
    Write-Host "❌ Failed to create schema`n" -ForegroundColor Red
    exit 1
}

# Show connection info
Write-Host "📋 Connection Information:" -ForegroundColor Cyan
Write-Host "=========================="
Write-Host "Host: localhost"
Write-Host "Port: 5432"
Write-Host "Database: supply_chain_dw"
Write-Host "Username: admin"
Write-Host "Password: adminpassword`n"

# Show next steps
Write-Host "🎯 Next Steps:" -ForegroundColor Cyan
Write-Host "=============="
Write-Host "1. Open VS Code in this directory"
Write-Host "2. Install SQLTools extension (if not already installed)"
Write-Host "3. Use the connection profile 'Torre Control - Local Dev'"
Write-Host "4. Open PgAdmin at http://localhost:5050"
Write-Host "   - Email: admin@dataco.com"
Write-Host "   - Password: adminpassword`n"

Write-Host "✅ Setup completed successfully!" -ForegroundColor Green

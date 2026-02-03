# 🛠️ SETUP GUÍA - Ambiente Profesional de Ingeniería de Datos
## Torre Control - Data Warehouse

**Documento:** Guía paso-a-paso para configurar VS Code Premium con Docker, PostgreSQL, y SQLTools

**Versión:** 1.0  
**Fecha:** 2 de Febrero de 2026  
**Nivel:** Senior Data Engineer

---

## 📋 ÍNDICE

1. [Requisitos Previos](#requisitos-previos)
2. [Instalación Docker](#instalación-docker)
3. [Estructura de Directorios](#estructura-de-directorios)
4. [Configuración de VS Code](#configuración-de-vs-code)
5. [Levantamiento de Servicios](#levantamiento-de-servicios)
6. [Verificación y Testing](#verificación-y-testing)
7. [Troubleshooting](#troubleshooting)

---

## 🔧 Requisitos Previos

### Sistema Operativo
- **Windows 10/11** (con WSL 2)
- **macOS 10.15+** (Intel o Apple Silicon)
- **Linux** (cualquier distribución moderna)

### Software Requerido
| Software | Versión Mínima | Propósito |
|----------|----------------|-----------|
| Docker Desktop | 4.20+ | Contenerización de PostgreSQL |
| VS Code | 1.80+ | IDE y editor SQL |
| Git | 2.30+ | Control de versiones |
| Python | 3.8+ | ETL scripts (opcional para fase 2) |

### Hardware Recomendado
- CPU: 4+ cores
- RAM: 8GB mínimo (16GB recomendado)
- Disk: 20GB disponible

---

## 🐳 Instalación Docker

### Windows 11/10 (WSL 2)

**Paso 1: Habilitar WSL 2**
```powershell
# Ejecutar PowerShell como Administrador
wsl --install

# Reiniciar computadora
Restart-Computer
```

**Paso 2: Instalar Docker Desktop**
1. Descargar desde https://www.docker.com/products/docker-desktop
2. Ejecutar instalador
3. Seleccionar "Use WSL 2 instead of Hyper-V" (si aparece)
4. Completar instalación y reiniciar

**Paso 3: Verificar Instalación**
```powershell
docker --version
docker run hello-world
```

### macOS

```bash
# Usando Homebrew
brew install docker
brew install --cask docker

# O descargar desde https://www.docker.com/products/docker-desktop
# Abrir archivo DMG y arrastrar Docker a Applications
```

### Linux

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo usermod -aG docker $USER
newgrp docker
```

---

## 📁 Estructura de Directorios

```
Proyecto_TorreContol/
├── docker-compose.yml          ← 🔑 Definición de servicios
├── .gitignore
├── .env.example                ← Configuración de ejemplo
│
├── data/
│   ├── raw/                    ← 📥 CSV del ERP (sin modificar)
│   │   ├── DataCoSupplyChainDataset.csv
│   │   ├── DescriptionDataCoSupplyChain.csv
│   │   └── tokenized_access_logs.csv
│   └── processed/              ← 📤 Datos transformados
│       └── (vacío - se genera en Phase 2)
│
├── sql/
│   ├── ddl/
│   │   └── 01_schema_base.sql   ← 🔑 Definición de tablas
│   └── queries/
│       └── q1_q5_strategic_questions.sql  ← 🔍 Consultas analíticas
│
├── scripts/
│   ├── setup.ps1                ← Setup para Windows
│   ├── setup.sh                 ← Setup para macOS/Linux
│   ├── health-check.ps1         ← Verificación Windows
│   ├── health-check.sh          ← Verificación macOS/Linux
│   ├── load_data.py             ← (Crear en Phase 2)
│   └── transform_data.py        ← (Crear en Phase 2)
│
├── .vscode/
│   ├── extensions.json          ← Extensiones recomendadas
│   ├── settings.json            ← Configuración de workspace
│   └── launch.json              ← (Opcional: debugging)
│
├── PBIX/
│   ├── TorreControl_v0.1.pbix   ← Power BI dashboard
│   └── Emoticones/
│
└── docs/
    ├── SETUP_GUIDE.md           ← Este archivo
    ├── README.md
    ├── CONTEXTO_ESTRATEGICO.md
    └── ...
```

---

## 🎨 Configuración de VS Code

### 1. Instalar Extensiones Recomendadas

**Opción A: Automática**
```
1. Abre VS Code en Proyecto_TorreContol/
2. VS Code detectará .vscode/extensions.json
3. Click en "Install Recommended Extensions"
```

**Opción B: Manual**
```
Presiona Ctrl+Shift+X (o Cmd+Shift+X en Mac) y busca:
- SQLTools
- SQLTools Driver for PostgreSQL
- Docker
- Rainbow CSV
- Markdown All in One
- Python
- Ruff (linter)
```

### 2. Importar Perfil de Conexión SQL

**Archivo:** `.vscode/settings.json` ya contiene la configuración.

**Verificar conexión:**
1. Click en SQLTools icon (left sidebar)
2. Click en "Torre Control - Local Dev"
3. Si está verde ✅ = conexión correcta

### 3. Configurar Workspace Settings

Los archivos ya están en `.vscode/`:
- `settings.json` - Configuración de editor + SQLTools
- `extensions.json` - Extensiones recomendadas

**Customización adicional (opcional):**
```json
// .vscode/settings.json
{
  "editor.fontSize": 12,
  "editor.formatOnSave": true,
  "files.autoSave": "onFocusChange",
  "[sql]": {
    "editor.tabSize": 2,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

---

## 🚀 Levantamiento de Servicios

### Paso 1: Inicializar Docker Compose

**Windows (PowerShell):**
```powershell
cd Proyecto_TorreContol
.\scripts\setup.ps1
```

**macOS/Linux (Bash):**
```bash
cd Proyecto_TorreContol
chmod +x scripts/*.sh
./scripts/setup.sh
```

**¿Qué hace setup?**
1. ✅ Verifica Docker instalado
2. ✅ Levanta containers (PostgreSQL + PgAdmin)
3. ✅ Espera a que PostgreSQL esté ready
4. ✅ Ejecuta DDL para crear schema
5. ✅ Imprime credenciales de acceso

### Paso 2: Verificar Servicios

**Windows:**
```powershell
.\scripts\health-check.ps1
```

**macOS/Linux:**
```bash
./scripts/health-check.sh
```

**Output esperado:**
```
✅ Docker is running
✅ PostgreSQL container is running
✅ PostgreSQL is responding
✅ DW schema exists
✅ Tables in DW schema: 7
```

### Paso 3: Verificar Acceso

**PostgreSQL (via SQLTools en VS Code):**
1. Click en SQLTools (left panel)
2. "Torre Control - Local Dev" debe mostrar verde
3. Expandir y ver tablas: dim_customer, fact_orders, etc.

**PgAdmin (Web):**
```
URL: http://localhost:5050
Email: admin@dataco.com
Password: adminpassword
```

---

## ✅ Verificación y Testing

### Test 1: Conexión a PostgreSQL

**Método A: SQLTools en VS Code**
```sql
SELECT version();
```
→ Si retorna versión de PostgreSQL ✅

**Método B: Terminal**
```powershell
docker exec supply_chain_db psql -U admin -d supply_chain_dw -c "SELECT 1;"
```
→ Output: `1` ✅

### Test 2: Schema y Tablas

```sql
-- En VS Code SQLTools
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'dw' 
ORDER BY table_name;
```

**Output esperado:**
```
dim_customer
dim_date
dim_geography
dim_product
etl_log
fact_orders
stg_raw_orders
```

### Test 3: Vistas Analíticas

```sql
SELECT * FROM dw.v_otif_by_market LIMIT 5;
```

→ Debe retornar resultados vacíos (aún sin datos cargados) ✅

### Test 4: Ejecutar Queries Q1-Q5

```sql
-- Abre: sql/queries/q1_q5_strategic_questions.sql
-- Ejecuta cualquier query
-- Si retorna resultados vacíos = OK (sin datos aún)
```

---

## 🔄 Flujo Completo de Setup

```
┌─────────────────────────────────────┐
│ 1. Verificar Docker instalado       │
└────────────┬────────────────────────┘
             ⬇️
┌─────────────────────────────────────┐
│ 2. docker-compose up -d             │
│    (PostgreSQL + PgAdmin)           │
└────────────┬────────────────────────┘
             ⬇️
┌─────────────────────────────────────┐
│ 3. Esperar PostgreSQL ready         │
│    (health check)                   │
└────────────┬────────────────────────┘
             ⬇️
┌─────────────────────────────────────┐
│ 4. Ejecutar DDL script              │
│    (crear schema + tables)          │
└────────────┬────────────────────────┘
             ⬇️
┌─────────────────────────────────────┐
│ 5. Conectar SQLTools en VS Code     │
└────────────┬────────────────────────┘
             ⬇️
┌─────────────────────────────────────┐
│ ✅ LISTO PARA FASE 2 (Load Data)    │
└─────────────────────────────────────┘
```

---

## 🆘 Troubleshooting

### ❌ Error: "Docker daemon is not running"

**Solución:**
```powershell
# Windows: Abre Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker.exe"
Start-Sleep -Seconds 30

# Intenta nuevo docker-compose up -d
```

### ❌ Error: "port 5432 already in use"

**Solución:**
```powershell
# Detener contenedores conflictivos
docker-compose down

# Esperar 10 segundos
Start-Sleep -Seconds 10

# Levantar nuevamente
docker-compose up -d
```

### ❌ Error: "pg_isready" command not found

**Solución:**
```bash
# El comando está dentro del contenedor
# No necesitas ejecutarlo locally

# Verifica que el contenedor esté running
docker ps | grep supply_chain_db
```

### ❌ SQLTools No Ve la Conexión

**Solución:**
1. Abre `.vscode/settings.json`
2. Verifica host: `localhost`, port: `5432`
3. Verifica usuario: `admin`, contraseña: `adminpassword`
4. Reinicia VS Code (Ctrl+Shift+P → Developer: Reload Window)
5. Click en SQLTools → "Clear all connections" → Reload

### ❌ PgAdmin No Accesible en localhost:5050

**Solución:**
```bash
# Verifica que PgAdmin está running
docker ps | grep pgadmin

# Si no aparece, levanta manualmente
docker-compose up -d pgadmin

# Espera 30 segundos y abre http://localhost:5050
```

### ❌ Error "FATAL: database 'supply_chain_dw' does not exist"

**Solución:**
```powershell
# El script de setup debería haber creado la BD
# Si no, ejecuta DDL manualmente:

docker exec supply_chain_db psql -U admin postgres -f /sql/ddl/01_schema_base.sql
```

---

## 📚 Próximos Pasos (Después de Setup)

### Phase 2: Cargar Datos CSV a PostgreSQL

1. **Crear script:** `scripts/load_data.py`
2. **Instalar pandas:** `pip install pandas sqlalchemy psycopg2`
3. **Ejecutar:** `python scripts/load_data.py`

### Phase 3: Transformar Datos

1. **Crear script:** `scripts/transform_data.py`
2. **Mover datos:** staging → dimensiones → facts

### Phase 4: Conectar a Power BI

1. **Abrir:** `PBIX/TorreControl_v0.1.pbix`
2. **Data source:** PostgreSQL (localhost:5432)
3. **Importar tablas:** fact_orders + dim_*
4. **Refresh & Deploy**

---

## ✨ Best Practices

### 1. Persistencia de Datos
```bash
# Los datos persisten en volumen "pgdata"
# Incluso si apagas los containers

# ❌ NO HAGAS ESTO (pierde datos)
docker system prune -a

# ✅ SI NECESITAS LIMPIAR
docker-compose down --volumes  # ⚠️ Elimina datos
```

### 2. Backup de PostgreSQL
```bash
# Backup completo
docker exec supply_chain_db pg_dump -U admin supply_chain_dw > backup.sql

# Restaurar desde backup
docker exec -i supply_chain_db psql -U admin supply_chain_dw < backup.sql
```

### 3. Monitoreo de Logs
```bash
# Ver logs en tiempo real
docker-compose logs -f postgres

# Ver logs de PgAdmin
docker-compose logs -f pgadmin
```

---

## 🎯 Checklist Final

- [ ] Docker Desktop instalado y corriendo
- [ ] `docker-compose up -d` ejecutado exitosamente
- [ ] PostgreSQL container está running
- [ ] PgAdmin accesible en http://localhost:5050
- [ ] SQLTools conectado a "Torre Control - Local Dev"
- [ ] Schema `dw` existe con 7 tablas
- [ ] Vistas analíticas funcionan (v_otif_*, v_revenue_*, etc.)
- [ ] VS Code tiene extensiones recomendadas
- [ ] Scripts `setup.ps1` y `health-check.ps1` están listos
- [ ] `.gitignore` excluye archivos sensibles

---

**Si todo está ✅, ¡Estás listo para comenzar Phase 2: Data Loading!**

Próximo paso: [Crear script `load_data.py` para CSV → PostgreSQL]

---

**Última Actualización:** 2 de Febrero de 2026  
**Autor:** Data Engineering Team  
**Estado:** ✅ Verificado en Windows 11, macOS Ventura, Ubuntu 22.04

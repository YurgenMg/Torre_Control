# 🔗 Power BI - Conexión Completa (Guía Paso a Paso)

## 📋 Tabla de Contenidos

1. [Pre-Requisitos](#pre-requisitos)
2. [Opción A: Importar CSVs (RECOMENDADO)](#opción-a-importar-csvs-recomendado)
3. [Opción B: DirectQuery a PostgreSQL](#opción-b-directquery-a-postgresql)
4. [Configurar Relaciones](#configurar-relaciones)
5. [Crear Primeras Métricas](#crear-primeras-métricas)
6. [Validar Datos](#validar-datos)
7. [Troubleshooting](#troubleshooting)

---

## Pre-Requisitos

✅ **Verificar antes de comenzar:**

- [ ] `make run` fue ejecutado exitosamente
- [ ] Archivos en `Data/Processed/` existen:
  ```bash
  ls Data/Processed/fact_orders.csv
  ls Data/Processed/dim_customer.csv
  ls Data/Processed/dim_product.csv
  ls Data/Processed/dim_geography.csv
  ls Data/Processed/dim_date.csv
  ```
- [ ] Power BI Desktop instalado
- [ ] PostgreSQL corriendo (si usas Opción B): `make health`

---

## Opción A: Importar CSVs (RECOMENDADO) ⭐

**Por qué:** Más rápido (186K filas local), sin latencia de red, ideal para desarrollo.

### Paso 1: Abrir Power BI

1. Abre **Power BI Desktop**
2. Click: **File** → **New**
3. Deberías ver lienzo en blanco

### Paso 2: Get Data (Folder)

1. Click: **Home** tab → **Get Data** → **Folder**
   
   ![Get Data - Folder](imagenes/getdata-folder.png)

2. Busca carpeta:
   ```
   C:\Users\USUARIO\Documents\Yurgenpersonal\Tripleten\Portafolio\Proyecto_TorreContol\Data\Processed
   ```

3. Click: **Load**

⏳ **Espera 2-3 minutos** mientras carga 186K filas

### Paso 3: Seleccionar Tablas

En el diálogo de carga, deberías ver 5 CSVs:
- fact_orders
- dim_customer
- dim_product
- dim_geography
- dim_date

**Selecciona TODAS.**

### Paso 4: Transformar (Power Query)

1. Click: **Transform Data** (si aparece dialogo)
2. Verifica tipos:
   - Números: Whole Number o Decimal
   - Fechas: Date
   - Texto: Text

3. Click: **Close & Apply**

✅ Los datos ahora están en Power BI.

---

## Opción B: DirectQuery a PostgreSQL

**Cuándo usar:** Si necesitas datos siempre frescos en vivo.

### Paso 1: Instalar PostgreSQL Connector

Si Power BI no tiene el conector PostgreSQL:

1. Descarga driver: https://www.postgresql.org/download/windows/
2. Busca: "PostgreSQL ODBC Driver"
3. Instala
4. Reinicia Power BI Desktop

### Paso 2: Get Data (PostgreSQL)

1. **File** → **Get Data** → **More...**
2. Busca: **PostgreSQL Database**
3. Click: **Connect**

### Paso 3: Configurar Conexión

```
Server:   localhost:5433
Database: supply_chain_dw
```

Click: **OK**

### Paso 4: Credenciales

```
Username: admin
Password: adminpassword
```

Click: **Connect**

### Paso 5: Seleccionar Tablas

En Navigator, selecciona:
```
✅ dw.fact_orders
✅ dw.dim_customer
✅ dw.dim_product
✅ dw.dim_geography
✅ dw.dim_date
```

Click: **Load**

⚠️ **Nota:** DirectQuery puede ser lento con 186K filas. Si ves lentitud, vuelve a Opción A (CSVs).

---

## Configurar Relaciones

### Paso 1: Ir a Model View

Click: **Model** tab (izquierda)

Deberías ver las 5 tablas con sus campos.

### Paso 2: Crear Relaciones

Si las relaciones NO se crearon automáticamente, crea estas 4:

#### **Relación 1: Fact → Customers**
- Arrastra `customer_key` desde **fact_orders** hacia **dim_customer**
- Type: **One-to-Many**

#### **Relación 2: Fact → Products**
- Arrastra `product_key` desde **fact_orders** hacia **dim_product**
- Type: **One-to-Many**

#### **Relación 3: Fact → Geography**
- Arrastra `geography_key` desde **fact_orders** hacia **dim_geography**
- Type: **One-to-Many**

#### **Relación 4: Fact → Date**
- Arrastra `date_key` desde **fact_orders** hacia **dim_date**
- Type: **One-to-Many**

✅ Deberías ver líneas conectando las tablas.

---

## Crear Primeras Métricas

### Paso 1: Ir a Report View

Click: **Report** tab

### Paso 2: Crear Card 1 - Total Orders

1. Insert → **Card**
2. Drag `order_id` desde fact_orders → Card
3. El card mostrará: **186,638**

### Paso 3: Crear Card 2 - OTIF%

1. Insert → **Card**
2. En fact_orders, click derecho → **New Measure**
3. Escribe fórmula:

```dax
OTIF % = 
DIVIDE(
    SUMX(FILTER(fact_orders, fact_orders[is_otif] = 1), 1),
    COUNTA(fact_orders[order_id]),
    0
) * 100
```

4. Format: **Percentage** con 2 decimales
5. Drag al Card → Deberá mostrar **~40.86%**

### Paso 4: Crear Card 3 - Revenue at Risk

1. Insert → **Card**
2. Click derecho en fact_orders → **New Measure**
3. Escribe:

```dax
Revenue at Risk = SUM(fact_orders[sales]) * 
                 AVERAGE(fact_orders[late_delivery_risk])
```

4. Format: **Currency** ($)
5. Drag al Card → Deberá mostrar **~$21.7M**

---

## Validar Datos

### Números Esperados

| Métrica | Valor Esperado | Tu Power BI |
|---------|---|---|
| Total Orders | 186,638 | ___ ✓ |
| OTIF % | 40.86% | ___ ✓ |
| Revenue at Risk | ~$21.7M | ___ ✓ |
| Total Revenue | ~$37.98M | ___ ✓ |
| Customers | 5,000 | ___ ✓ |
| Products | 1,800 | ___ ✓ |
| Markets | 5 | ___ ✓ |

**Si tus números coinciden: ✅ CONEXIÓN EXITOSA**

---

## 5 Visualizaciones Siguientes

Una vez validado, crea estas visualizaciones:

### **View 1: OTIF Performance**
- KPI Card: OTIF %
- Matrix: OTIF % by Market & Segment
- Slicer: Date range

### **View 2: Revenue at Risk**
- Waterfall: Revenue by Delivery Status
- Top 10 Products by Risk
- Slicer: Customer Segment

### **View 3: VIP Churn Risk**
- Table: Top 10% Customers + Last 2 orders late?
- Risk Score by Customer
- Filter: Show only Top 10% by Sales

### **View 4: Geographic Performance**
- Map: Market → OTIF % by region
- Drill-down: Market → Region → State
- Heatmap: Color by OTIF %

### **View 5: Anomaly Detection**
- Scatter: Days to Ship vs. Discount Rate
- Table: Suspicious Orders (OTIF risk + fraud flags)
- Filter: Order Status = SUSPECTED_FRAUD

---

## Troubleshooting

### Error: "Cannot connect to Data Source"

**Si Opción A (CSVs):**
- [ ] Data/Processed/ existe y tiene archivos
- [ ] Ruta es correcta
- [ ] CSVs no están corrompidos

**Solución:**
```bash
make export    # Regenerar CSVs
make validate  # Validar integridad
```

### Error: "ModuleNotFoundError: No module named 'psycopg2'"

**Causa:** Falta driver PostgreSQL ODBC

**Solución (si usas Opción B):**
```bash
# Windows: Download https://www.postgresql.org/download/windows/
# Mac:     brew install postgresql
# Linux:   sudo apt-get install postgresql-client
```

### Slow Performance (DirectQuery)

**Causa:** 186K filas consultadas en vivo

**Solución:** Usa **Opción A (CSVs)** en su lugar

### CSVs show blank or no data

**Causa:** Archivo corrupto o incompleto

**Solución:**
```bash
make clean          # Remove old CSVs
make export         # Regenerate
```

Luego recarga en Power BI: **Refresh**

### Numbers don't match expected values

**Causa:** Relaciones no configuradas o datos incompletos

**Solución:**
1. Verifica relaciones en Model View
2. Ejecuta: `make health` (check row counts)
3. Regenera: `make export && make validate`

---

## 🎯 Próximos Pasos

1. ✅ Importa CSVs (Opción A recomendado)
2. ✅ Crea 3 cards para validar números
3. ✅ Crea 5 visualizaciones para Q1-Q5 estratégicas
4. ⭐ Publica a Power BI Service (nube) para compartir

---

## 📚 Referencias

- **Power Query Tutorial:** https://bit.ly/pbi-powerquery
- **DAX Formulas:** https://bit.ly/pbi-dax
- **Geographic Visualizations:** https://bit.ly/pbi-maps

---

**¿Dudas?** Consulta `QUICK_REFERENCE.md` o `AUDITORIA_ARQUITECTURA.md`

**Next:** Create dashboard pages for 5 strategic questions → Ready for Power BI Service!

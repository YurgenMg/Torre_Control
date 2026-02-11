# 🎯 Power BI Dashboard Torre Control - Guía Paso a Paso para Principiantes

**Proyecto:** Torre Control - Supply Chain Analytics  
**Nivel:** Principiante  
**Tiempo estimado:** 2-3 horas  
**Objetivo:** Crear un dashboard profesional ejecutivo para análisis logístico

---

## 📋 Tabla de Contenidos

1. [Preparación Previa](#1-preparación-previa)
2. [Instalación de Power BI Desktop](#2-instalación-de-power-bi-desktop)
3. [Exportar Datos del Proyecto](#3-exportar-datos-del-proyecto)
4. [Conectar Power BI a los Datos](#4-conectar-power-bi-a-los-datos)
5. [Crear el Modelo de Datos (Star Schema)](#5-crear-el-modelo-de-datos-star-schema)
6. [Crear Medidas DAX Esenciales](#6-crear-medidas-dax-esenciales)
7. [Página 1: Dashboard Ejecutivo](#7-página-1-dashboard-ejecutivo)
8. [Página 2: Análisis Geográfico](#8-página-2-análisis-geográfico)
9. [Página 3: Análisis de Clientes en Riesgo](#9-página-3-análisis-de-clientes-en-riesgo)
10. [Configurar Interactividad](#10-configurar-interactividad)
11. [Guardar y Publicar](#11-guardar-y-publicar)
12. [Checklist Final](#12-checklist-final)

---

## 1. Preparación Previa

### ✅ Verificar que tienes:

**A. Pipeline ETL completado**
```powershell
# En tu terminal de PowerShell, ejecuta:
cd "C:\Users\USUARIO\Documents\Yurgenpersonal\Tripleten\Portafolio\Proyecto_TorreContol"
.\.venv\Scripts\Activate.ps1
python scripts/transform_data.py
```

Si ves mensajes de éxito, continúa. Si hay errores, revisa primero la documentación del ETL.

**B. Archivos procesados disponibles**

Verifica que existan estos archivos en `Data/Processed/`:
- `dim_customer.csv` (o `.parquet`)
- `dim_product.csv`
- `dim_geography.csv`
- `dim_date.csv`
- `fact_orders.csv`

---

## 2. Instalación de Power BI Desktop

### Opción A: Microsoft Store (Recomendado)

1. Abre **Microsoft Store** en Windows
2. Busca **"Power BI Desktop"**
3. Haz clic en **Obtener** o **Instalar**
4. Espera a que se complete la instalación

### Opción B: Descarga Directa

1. Ve a: https://powerbi.microsoft.com/desktop/
2. Haz clic en **Descargar gratis**
3. Ejecuta el instalador `.exe`
4. Sigue el asistente de instalación

**⏱️ Tiempo:** 5-10 minutos

---

## 3. Exportar Datos del Proyecto

### Paso 3.1: Ejecutar el Script de Exportación

Vamos a convertir los datos a formato **Parquet**, que es 10-50 veces más rápido que CSV para Power BI.

```powershell
# Asegúrate de estar en el directorio del proyecto
cd "C:\Users\USUARIO\Documents\Yurgenpersonal\Tripleten\Portafolio\Proyecto_TorreContol"

# Activa el entorno virtual (si no está activo)
.\.venv\Scripts\Activate.ps1

# Ejecuta el exportador
python scripts/export_for_powerbi.py --format parquet
```

### Paso 3.2: Verificar que se crearon los archivos

```powershell
# Listar archivos Parquet
Get-ChildItem "Data\Processed\*.parquet"
```

Deberías ver:
```
dim_customer.parquet
dim_date.parquet
dim_geography.parquet
dim_product.parquet
fact_orders.parquet
```

### Paso 3.3: Verificar Campos Clave (Opcional pero Recomendado)

Para asegurarte de que los campos necesarios existen, puedes abrir Python y verificar:

```powershell
python
```

Luego ejecuta:
```python
import pandas as pd

# Leer fact_orders
df = pd.read_parquet('Data/Processed/fact_orders.parquet')

# Ver primeras filas
print(df.head())

# Ver nombres de columnas
print("\nColumnas disponibles:")
print(df.columns.tolist())

# Salir de Python
exit()
```

**Verifica que existan estas columnas clave:**
- ✅ `order_id`
- ✅ `customer_key`
- ✅ `product_key`
- ✅ `geo_key`
- ✅ `date_key`
- ✅ `sales`
- ✅ `late_delivery_risk`

**Solo estos 7 campos existen en la tabla de hechos.** Si no los ves, ejecuta nuevamente: `python scripts/transform_data.py`

**⏱️ Tiempo:** 2-3 minutos

---

## 4. Conectar Power BI a los Datos

### Paso 4.1: Abrir Power BI Desktop

1. Abre **Power BI Desktop**
2. En la ventana de inicio, haz clic en **Cargar datos** (o cierra la ventana de inicio)

### Paso 4.2: Conectar a la Carpeta de Datos

1. En la cinta superior, haz clic en **Obtener datos** → **Más...**
2. En el cuadro de búsqueda, escribe **"Carpeta"**
3. Selecciona **Carpeta** y haz clic en **Conectar**

![Obtener datos desde carpeta](../assets/powerbi_step1.png)

### Paso 4.3: Seleccionar la Carpeta

1. Haz clic en **Examinar**
2. Navega a: `C:\Users\USUARIO\Documents\Yurgenpersonal\Tripleten\Portafolio\Proyecto_TorreContol\Data\Processed`
3. Haz clic en **Seleccionar carpeta**
4. Haz clic en **Aceptar**

### Paso 4.4: Combinar Archivos

1. Power BI mostrará una lista de archivos en la carpeta
2. **NO hagas clic en "Combinar"** (eso mezclaría todo en una tabla)
3. En su lugar, haz clic en **Transformar datos**

### Paso 4.5: Crear Tablas Individuales

Estamos en **Power Query Editor** (el editor de ETL de Power BI).

**Para cada archivo Parquet:**

1. **dim_customer.parquet:**
   - En el panel izquierdo, haz clic derecho en la consulta inicial
   - Selecciona **Duplicar**
   - Nombra la nueva consulta: `dim_customer`
   - En el panel derecho (Pasos aplicados), haz clic en el último paso
   - Filtra para mostrar solo `dim_customer.parquet`:
     - Haz clic en la flecha del encabezado **Name**
     - Desmarca todo excepto `dim_customer.parquet`
     - Haz clic en **Aceptar**
   - Haz clic en el botón de dos flechas junto al encabezado **Content**
   - Selecciona **Aceptar** para expandir el contenido

2. **Repite el proceso para:**
   - `dim_date` (filtra por `dim_date.parquet`)
   - `dim_geography` (filtra por `dim_geography.parquet`)
   - `dim_product` (filtra por `dim_product.parquet`)
   - `fact_orders` (filtra por `fact_orders.parquet`)

### Paso 4.6: Eliminar Consulta Original

1. Haz clic derecho en la consulta inicial (sin nombre descriptivo)
2. Selecciona **Eliminar**
3. Confirma la eliminación

### Paso 4.7: Cargar los Datos

1. Haz clic en **Cerrar y aplicar** en la esquina superior izquierda
2. Espera a que Power BI cargue los datos (puede tardar 1-2 minutos)

**✅ Éxito:** Deberías ver 5 tablas en el panel **Datos** del lado derecho.

**⏱️ Tiempo:** 10-15 minutos

---

## 5. Crear el Modelo de Datos (Star Schema)

### Conceptos Clave (Explicación simple)

**Star Schema (Esquema en Estrella):**
- **Centro = Tabla de Hechos** (`fact_orders`): Transacciones, ventas, eventos
- **Puntas de la Estrella = Dimensiones** (`dim_*`): Descripciones, categorías

**Relaciones:**
- **1:* (Uno a Muchos):** Una dimensión (1 cliente) se relaciona con muchos hechos (muchas órdenes)
- **Dirección del filtro:** Las dimensiones filtran los hechos (no al revés)

### Paso 5.1: Ir a la Vista de Modelo

1. En el panel izquierdo, haz clic en el ícono **Modelo** (tres cuadros conectados)
2. Verás todas tus tablas como cajas

### Paso 5.2: Organizar Visualmente las Tablas

Arrastra las tablas para que se vean así:

```
        dim_date
           |
           |
dim_customer ---- fact_orders ---- dim_product
           |
           |
      dim_geography
```

`fact_orders` debe estar en el centro.

### Paso 5.3: Crear Relaciones

**Relación 1: fact_orders → dim_customer**

1. Arrastra el campo `customer_id` de `fact_orders`
2. Suéltalo sobre el campo `customer_id` de `dim_customer`
3. En el cuadro de diálogo:
   - **Cardinalidad:** Muchos a uno (*:1)
   - **Dirección del filtro cruzado:** Única (Single)
   - Haz clic en **Aceptar**

**Relación 2: fact_orders → dim_product**

1. Arrastra `product_card_id` de `fact_orders`
2. Suéltalo sobre `product_card_id` de `dim_product`
3. Confirma: **Muchos a uno (*:1)**, **Única**

**Relación 3: fact_orders → dim_geography**

1. Arrastra `geography_key` de `fact_orders`
2. Suéltalo sobre `geography_key` de `dim_geography`
3. Confirma: **Muchos a uno (*:1)**, **Única**

**Relación 4: fact_orders → dim_date**

1. Arrastra `date_key` de `fact_orders`
2. Suéltalo sobre `date_key` de `dim_date`
3. Confirma: **Muchos a uno (*:1)**, **Única**

### Paso 5.4: Marcar la Tabla de Fechas

**Importante:** Para que funcionen las funciones de inteligencia temporal.

1. Haz clic derecho en la tabla `dim_date`
2. Selecciona **Marcar como tabla de fechas**
3. Elige la columna: **full_date** (o **date_key** si no existe `full_date`)
4. Haz clic en **Aceptar**

### Paso 5.5: Verificar Relaciones

Deberías ver líneas conectando `fact_orders` con todas las dimensiones. Cada línea debe tener:
- **1** en el lado de la dimensión
- ***** (asterisco) en el lado de `fact_orders`

**✅ Modelo completado:** ¡Tu star schema está listo!

**⏱️ Tiempo:** 10 minutos

---

## 6. Crear Medidas DAX Esenciales

### ¿Qué es DAX?
**DAX (Data Analysis Expressions)** es el lenguaje de fórmulas de Power BI. Es similar a Excel, pero más potente.

### 📊 Campos Disponibles en fact_orders

Antes de crear medidas, es importante conocer los campos que **realmente existen** en tu tabla `fact_orders`:

| Campo | Tipo | Descripción | Uso |
|-------|------|-------------|-----|
| `order_id` | Texto | ID único de la orden | Identificador, conteo de órdenes |
| `customer_key` | Numérico | Foreign key a `dim_customer` | Relación con clientes |
| `product_key` | Numérico | Foreign key a `dim_product` | Relación con productos |
| `geo_key` | Numérico | Foreign key a `dim_geography` | Relación con geografía |
| `date_key` | Numérico | Foreign key a `dim_date` | Relación con fechas |
| `sales` | Numérico | Monto en $ de la venta | Cálculo de revenue |
| `late_delivery_risk` | Numérico | **0** = a tiempo ✅, **1** = tarde ❌ | **Métrica clave para OTIF** |

**⚠️ Importante:** Los campos `order_status`, `delivery_status`, `days_for_shipping_real` **NO están en fact_orders**. Están en los datos crudos pero no se incluyeron en el modelo dimensional final.

---

### Paso 6.1: Crear una Tabla de Medidas

Es una buena práctica agrupar todas las medidas en una tabla vacía.

1. Ve a la vista **Informe** (ícono de gráfico de barras)
2. En la cinta superior, haz clic en **Obtener datos** → **Más...**
3. Busca **"Consulta en blanco"**
4. Selecciona **Consulta en blanco** y haz clic en **Conectar**
5. En Power Query, no hagas nada, solo haz clic en **Cerrar y aplicar**
6. En el panel **Datos**, haz clic derecho en la nueva tabla
7. Renómbrala a: `_Medidas`

### Paso 6.2: Medida 1 - Total de Ventas

```dax
Total Sales = SUM(fact_orders[sales])
```

**Cómo crearla:**
1. Haz clic derecho en la tabla `_Medidas`
2. Selecciona **Nueva medida**
3. En la barra de fórmulas (arriba), escribe la fórmula
4. Presiona **Enter**

### Paso 6.3: Medida 2 - Cantidad de Órdenes

```dax
Order Count = DISTINCTCOUNT(fact_orders[order_id])
```

**DISTINCTCOUNT** cuenta valores únicos (evita contar la misma orden dos veces si tiene múltiples productos).

### Paso 6.4: Medida 3 - OTIF % (On-Time In-Full)

**Esta es la métrica clave del proyecto.**

```dax
OTIF % = 
VAR OnTimeOrders = 
    CALCULATE(
        COUNTROWS(fact_orders),
        fact_orders[late_delivery_risk] = 0
    )
VAR TotalOrders = COUNTROWS(fact_orders)
RETURN
    DIVIDE(OnTimeOrders, TotalOrders, 0)
```

**Explicación:**
- `VAR` crea una variable (calcula una sola vez, mejora rendimiento)
- `late_delivery_risk = 0` significa **entrega a tiempo** ✅
- `late_delivery_risk = 1` significa **entrega tardía** ❌
- `CALCULATE` cambia el contexto del filtro
- `DIVIDE` divide de forma segura (evita errores si el denominador es cero)
- La medida devuelve un decimal (0.95 = 95%)

**📍 Campos disponibles en fact_orders:**
Tu tabla `fact_orders` solo contiene estos campos del ETL:
- `order_id`, `customer_key`, `product_key`, `geo_key`, `date_key`
- `sales` (monto de venta)
- `late_delivery_risk` (0 = a tiempo, 1 = tarde)

### Paso 6.5: Medida 4 - Revenue at Risk

```dax
Revenue at Risk = 
CALCULATE(
    SUM(fact_orders[sales]),
    fact_orders[late_delivery_risk] = 1
)
```

**Explicación:**
- Suma todas las ventas donde `late_delivery_risk = 1` (entregas tardías)
- Más simple y eficiente que usar `FILTER`

### Paso 6.6: Medida 5 - Late Orders %

**Porcentaje de entregas tardías:**

```dax
Late Orders % = 
DIVIDE(
    CALCULATE(COUNTROWS(fact_orders), fact_orders[late_delivery_risk] = 1),
    COUNTROWS(fact_orders),
    0
)
```

**Explicación:**
- Cuenta cuántas filas tienen `late_delivery_risk = 1` (tarde)
- Divide por el total de órdenes
- Devuelve un decimal (0.15 = 15%)

### Paso 6.7: Formatear las Medidas

**Para porcentajes:**
1. Selecciona la medida `OTIF %` en el panel **Datos**
2. En la cinta **Herramientas de medida**, haz clic en **%** (Porcentaje)
3. Ajusta los decimales a **1** (95.5%)

**Para moneda:**
1. Selecciona `Total Sales`
2. Haz clic en **$** (Moneda)
3. Elige el símbolo de tu divisa (USD $, EUR €, etc.)

**✅ Medidas creadas:** Ahora podemos construir visuales.

**⏱️ Tiempo:** 15 minutos

---

## 7. Página 1: Dashboard Ejecutivo

### Objetivo de esta página:
**Mostrar KPIs críticos en 10 segundos o menos** para que un ejecutivo tome decisiones rápidas.

### Principio de diseño:
**"Menos es más"** - Máximo 5-7 visuales por página.

---

### Paso 7.1: Renombrar la Página

1. En la parte inferior, haz clic derecho en la pestaña **Página 1**
2. Selecciona **Renombrar página**
3. Escribe: **Resumen Ejecutivo**

### Paso 7.2: Configurar el Lienzo

1. Ve a **Vista** → **Configuración de página**
2. En el panel derecho, selecciona:
   - **Tipo:** 16:9 (pantallas modernas)
   - **Fondo:** Elige un color corporativo suave (gris claro, azul pálido)

---

### Paso 7.3: Crear KPI Cards (Tarjetas)

**KPI 1: OTIF %**

1. En **Visualizaciones**, selecciona el ícono de **Tarjeta** (cuadro con número)
2. Arrastra la medida `OTIF %` al campo **Campos**
3. Posiciona la tarjeta en la esquina superior izquierda
4. Haz clic en **Formato de visual** (rodillo de pintura)
5. **Etiqueta de categoría** → Escribe: **"OTIF %"**
6. **Etiqueta de datos:**
   - Tamaño del texto: **36**
   - Color: Verde si >95%, rojo si <90%

**KPI 2: Total Sales**

1. Crea otra **Tarjeta**
2. Arrastra `Total Sales`
3. Posiciona junto a OTIF %
4. Etiqueta: **"Ventas Totales"**

**KPI 3: Revenue at Risk**

1. Crea otra **Tarjeta**
2. Arrastra `Revenue at Risk`
3. Posiciona junto a Total Sales
4. Etiqueta: **"Revenue en Riesgo"**
5. Color: Rojo (alerta)

**KPI 4: Late Orders %**

1. Crea otra **Tarjeta**
2. Arrastra `Late Orders %`
3. Posiciona junto a Revenue at Risk
4. Etiqueta: **"% Entregas Tardías"**

---

### Paso 7.4: Gráfico de Línea - OTIF % por Mes

**Propósito:** Ver tendencia de desempeño logístico en el tiempo.

1. Selecciona **Gráfico de líneas** en Visualizaciones
2. **Eje X:** Arrastra `dim_date[mes]` (o `month_name`)
3. **Eje Y:** Arrastra `OTIF %`
4. Posiciona el gráfico debajo de las tarjetas KPI
5. **Formato:**
   - Título: **"Tendencia OTIF % Mensual"**
   - Línea de datos: Grosor 3, color corporativo
   - Añadir **Línea de objetivo** en 95% (umbral de excelencia)

---

### Paso 7.5: Gráfico de Barras - OTIF % por Market

**Propósito:** Identificar mercados con problemas logísticos.

1. Selecciona **Gráfico de barras horizontales**
2. **Eje Y:** Arrastra `dim_geography[market]`
3. **Eje X:** Arrastra `OTIF %`
4. Posiciona al lado del gráfico de líneas
5. **Formato:**
   - Título: **"OTIF % por Mercado"**
   - **Formato condicional:** Rojo si <90%, verde si >95%
     - Clic en `OTIF %` → **Formato condicional** → **Color de fondo**
     - Regla: Si `OTIF %` < 0.90 → Rojo
     - Regla: Si `OTIF %` > 0.95 → Verde

---

### Paso 7.6: Mapa Geográfico

**Propósito:** Vista visual de desempeño por región.

1. Selecciona **Mapa de formas de Azure** (o **Mapa**)
2. **Ubicación:** Arrastra `dim_geography[market]`
3. **Tamaño de burbuja:** Arrastra `Total Sales`
4. **Saturación de color:** Arrastra `OTIF %`
   - Colores: Verde (alto) → Rojo (bajo)
5. Posiciona el mapa en la parte inferior derecha

---

### Paso 7.7: Narrativa Inteligente

**Propósito:** Genera automáticamente un resumen en texto de los datos.

1. Selecciona **Narrativa inteligente** en Visualizaciones
2. Posiciona en la parte inferior izquierda
3. Power BI generará frases como:
   > "El mercado LATAM representa el 35% de las ventas, con un OTIF de 87%, por debajo del objetivo del 95%."

---

**✅ Página 1 completada:** Dashboard ejecutivo listo.

**⏱️ Tiempo:** 20 minutos

---

## 8. Página 2: Análisis Geográfico

### Paso 8.1: Crear Nueva Página

1. Haz clic en el **+** junto a **Resumen Ejecutivo**
2. Renombra la página: **Análisis Geográfico**

---

### Paso 8.2: Crear Jerarquía Geográfica

**Antes de crear visuales, configuramos la jerarquía:**

1. Ve a la vista **Datos** (ícono de tabla)
2. En el panel **Datos**, busca la tabla `dim_geography`
3. Haz clic derecho en el campo `market`
4. Selecciona **Crear jerarquía**
5. Power BI crea: `market Hierarchy`
6. Arrastra estos campos en orden a la jerarquía:
   - `region`
   - `country`
   - `city`

Resultado:
```
market Hierarchy
  └─ market
     └─ region
        └─ country
           └─ city
```

---

### Paso 8.3: Mapa con Drill-Down

1. Vuelve a la vista **Informe**
2. Crea un **Mapa de formas**
3. **Ubicación:** Arrastra `market Hierarchy` (la jerarquía completa)
4. **Tamaño:** `Total Sales`
5. **Color:** `OTIF %`
6. **Habilitar drill-down:**
   - Haz clic en el ícono de **Flecha hacia abajo** en la barra del visual
7. Expande el mapa para ocupar la mitad de la página

**Cómo usar:**
- Haz clic en una región → Power BI hace "zoom" a estados
- Haz clic en un estado → Power BI muestra ciudades
- Haz clic en el **ícono de flecha hacia arriba** para volver

---

### Paso 8.4: Matriz Detallada

**Propósito:** Tabla con números exactos.

1. Selecciona **Matriz**
2. **Filas:** Arrastra `market Hierarchy`
3. **Valores:** Arrastra:
   - `Total Sales`
   - `Order Count`
   - `OTIF %`
   - `Revenue at Risk`
4. Posiciona al lado del mapa
5. **Formato condicional:**
   - Selecciona `OTIF %` → **Formato condicional** → **Barras de datos**
   - Elige escala de colores: Verde (alto) → Rojo (bajo)

---

### Paso 8.5: Gráfico de Dispersión - Ventas vs. OTIF %

**Propósito:** Identificar mercados de alto valor con bajo desempeño.

1. Selecciona **Gráfico de dispersión**
2. **Eje X:** `Total Sales`
3. **Eje Y:** `OTIF %`
4. **Valores:** `dim_geography[market]`
5. **Tamaño:** `Order Count`
6. Posiciona en la parte inferior
7. **Interpretación:**
   - **Cuadrante superior derecho:** Alto OTIF, altas ventas = ✅ Excelente
   - **Cuadrante inferior derecho:** Bajo OTIF, altas ventas = ⚠️ Crisis (ventas en riesgo)
   - **Cuadrante inferior izquierdo:** Bajo OTIF, bajas ventas = ❌ Cerrar mercado

---

**✅ Página 2 completada:** Análisis geográfico con drill-down.

**⏱️ Tiempo:** 15 minutos

---

## 9. Página 3: Análisis de Clientes en Riesgo

### Objetivo:
**Identificar clientes VIP con entregas tardías consecutivas** para el equipo de retención.

---

### Paso 9.1: Crear Nueva Página

1. Crea una nueva página: **Clientes en Riesgo**

---

### Paso 9.2: Matriz de Clientes VIP

1. Selecciona **Matriz**
2. **Filas:** Arrastra estos campos de `dim_customer`:
   - `customer_name`
   - `customer_email`
   - `customer_segment`
3. **Valores:** Arrastra:
   - `Sales per customer` (de `dim_customer`)
   - `Order Count`
   - `OTIF %`
   - `Late Orders %` (o `Avg Delay Days`)
4. **Ordenar:** Haz clic en el encabezado `Sales per customer` para ordenar de mayor a menor
5. Expande la matriz para ocupar la mayoría de la página

---

### Paso 9.3: Filtrar Solo Top 10% (VIP)

1. Selecciona la matriz
2. En **Filtros** (panel derecho), ve a **Filtros en este objeto visual**
3. Arrastra `Sales per customer` al área de filtros
4. Cambia el tipo de filtro a **Top N**
5. Configura:
   - **Mostrar elementos:** Top 10 (ajusta según prefieras)
   - **Por valor:** `Sales per customer`
6. Haz clic en **Aplicar filtro**

---

### Paso 9.4: Gráfico de Barras - Segmento de Cliente

1. Selecciona **Gráfico de barras apiladas**
2. **Eje Y:** `customer_segment`
3. **Eje X:** `Revenue at Risk`
4. Posiciona en la parte superior
5. Título: **"Revenue en Riesgo por Segmento"**

---

### Paso 9.5: Crear Página de Drill-Through (Avanzado)

**Propósito:** Al hacer clic derecho en un cliente, ver todas sus órdenes.

1. Crea una nueva página: **Detalle de Cliente**
2. Haz clic derecho en la pestaña de página → **Ocultar página** (no aparecerá en navegación normal)
3. En **Visualizaciones**, busca **Drill through**
4. Arrastra `dim_customer[customer_name]` al área **Drill through**
5. Crea una **Tabla** con:
   - `fact_orders[order_id]`fecha desde la dimensión)
   - `dim_customer[customer_name]` (nombre desde la dimensión)r_date` si existe en fact_orders)
   - `fact_orders[delivery_status]`
   - `fact_orders[late_delivery_risk]`
   - `fact_orders[sales]`
6. Añade un botón **Atrás** (para volver):
   - **Insertar** → **Botones** → **Atrás**

**Cómo usar:**
- En la página de Clientes en Riesgo, haz clic derecho en un nombre de cliente
- Selecciona **Drill through** → **Detalle de Cliente**
- Power BI mostrará solo las órdenes de ese cliente

---

**✅ Página 3 completada:** Análisis de retención.

**⏱️ Tiempo:** 15 minutos

---

## 10. Configurar Interactividad

### Paso 10.1: Segmentaciones (Slicers)

**Propósito:** Permitir al usuario filtrar todo el dashboard.

1. Ve a **Resumen Ejecutivo**
2. Selecciona **Segmentación de datos** en Visualizaciones
3. **Campo:** Arrastra `dim_date[year]`
4. Posiciona en la esquina superior derecha
5. **Formato:**
   - Estilo: **Botones de opción** (para selección única)
   - O usa **Selector desplegable** (para ahorrar espacio)

**Replica la segmentación en todas las páginas:**
1. Haz clic derecho en la segmentación
2. **Copiar**
3. Ve a **Análisis Geográfico**
4. **Pegar** (Ctrl+V)
5. Repite para **Clientes en Riesgo**

---

### Paso 10.2: Sincronizar Segmentaciones

**Para que un filtro afecte todas las páginas:**

1. Selecciona cualquier segmentación
2. Ve a **Vista** → **Sincronizar segmentaciones**
3. En el panel que aparece:
   - Marca todas las páginas en **Sincronizar**
   - Marca todas las páginas en **Visible**
4. Cierra el panel

Ahora, si cambias el año en cualquier página, todas las páginas se actualizan.

---

### Paso 10.3: Crear Marcadores (Bookmarks)

**Propósito:** Cambiar entre vistas con un clic (ejemplo: "Vista de Ventas" vs. "Vista de Logística").

1. Ve a **Vista** → **Marcadores**
2. Configura tu dashboard en "Vista de Ventas" (muestra solo gráficos de ventas)
3. Haz clic en **Agregar** en el panel de marcadores
4. Renombra el marcador: **Vista Ventas**
5. Configura tu dashboard en "Vista de Logística" (muestra OTIF, entregas)
6. Agrega otro marcador: **Vista Logística**

**Crear botones para cambiar de vista:**
1. **Insertar** → **Botones** → **Botón en blanco**
2. **Formato de botón:**
   - Texto: **Ventas**
   - Acción: Activada
   - Tipo: **Marcador**
   - Marcador: **Vista Ventas**
3. Repite para **Vista Logística**

---

**✅ Interactividad configurada:** Dashboard profesional interactivo.

**⏱️ Tiempo:** 10 minutos

---

## 11. Guardar y Publicar

### Paso 11.1: Guardar el Archivo

1. **Archivo** → **Guardar como**
2. Navega a: `C:\Users\USUARIO\Documents\Yurgenpersonal\Tripleten\Portafolio\Proyecto_TorreContol\PBIX`
3. Nombre del archivo: **Torre_Control_Dashboard_Final.pbix**
4. Haz clic en **Guardar**

---

### Paso 11.2: Exportar a PDF (para presentaciones)

1. **Archivo** → **Exportar** → **Exportar a PDF**
2. Elige qué páginas incluir
3. Guarda el PDF en la carpeta `docs/reports/`

---

### Paso 11.3: Publicar en Power BI Service (Opcional)

**Requisitos:** Cuenta de Microsoft 365 o Power BI Pro.

1. Haz clic en **Publicar** en la cinta superior
2. Selecciona **Mi área de trabajo**
3. Haz clic en **Seleccionar**
4. Espera a que se complete la publicación
5. Haz clic en **Abrir en Power BI** para ver tu dashboard en línea

**Configurar actualizaciones programadas:**
- En Power BI Service, ve a **Configuración** del dataset
- Configura **Actualización programada** (diaria, semanal, etc.)

---

**✅ Dashboard guardado y compartible.**

**⏱️ Tiempo:** 5 minutos

---

## 12. Checklist Final

### Modelo de Datos ✅
- [ ] 5 tablas cargadas (4 dimensiones + 1 hecho)
- [ ] 4 relaciones creadas (todas 1:*)
- [ ] `dim_date` marcada como tabla de fechas
- [ ] Jerarquía geográfica creada

### Medidas DAX ✅
- [ ] Total Sales
- [ ] Order Count
- [ ] OTIF %
- [ ] Revenue at Risk
- [ ] Late Orders % (o Avg Delay Days)
- [ ] Todas las medidas formateadas correctamente

### Páginas del Dashboard ✅
- [ ] **Página 1:** Resumen Ejecutivo (4 KPIs + 3 gráficos)
- [ ] **Página 2:** Análisis Geográfico (mapa drill-down + matriz)
- [ ] **Página 3:** Clientes en Riesgo (matriz VIP + segmentación)
- [ ] **Página oculta:** Detalle de Cliente (drill-through)

### Interactividad ✅
- [ ] Segmentaciones de fecha sincronizadas
- [ ] Marcadores configurados (opcional)
- [ ] Drill-through funcionando
- [ ] Formato condicional aplicado

### Publicación ✅
- [ ] Archivo guardado en `PBIX/`
- [ ] PDF exportado (opcional)
- [ ] Publicado en Power BI Service (opcional)

---

## 🎉 ¡Felicitaciones!

Has creado un dashboard profesional de clase empresarial con:
- ✅ Modelo de datos optimizado (Star Schema)
- ✅ Medidas DAX con mejores prácticas (uso de VAR)
- ✅ Visualizaciones ejecutivas y operacionales
- ✅ Interactividad avanzada (drill-down, drill-through, slicers)

---

## 📚 Recursos de Aprendizaje Adicionales

### Para profundizar:
1. **DAX avanzado:** https://dax.guide/
2. **Patrones de diseño:** https://www.sqlbi.com/dax-patterns/
3. **Certificación PL-300:** Microsoft Power BI Data Analyst

### Próximos pasos:
- Añadir análisis predictivo (Machine Learning)
- Implementar Row-Level Security (RLS) para acceso por roles
- Crear alertas automáticas cuando OTIF% < 90%

---

## 🆘 Soporte

**¿Tienes problemas?**
- **Documentación del proyecto:** `docs/`
- **Guía de Power BI:** `docs/POWERBI_GUIDE.md`
- **GitHub Issues:** https://github.com/YurgenMg/Torre_Control

---

**Creado por:** Torre Control Engineering Team  
**Última actualización:** 10 de febrero de 2026  
**Versión:** 1.0

# 📚 EXPLICACIÓN COMPLETA DEL PROYECTO - Dashboard Cobranzas

## 🔍 PROBLEMA ACTUAL

**La aplicación NO está extrayendo datos de Odoo** - Esto se debe a que falta la configuración correcta del archivo `.env` o las credenciales están incorrectas.

---

## 🏗️ ARQUITECTURA DEL PROYECTO

### Flujo de Datos (De Odoo al Frontend)

```
┌──────────────┐
│   ODOO ERP   │ (Sistema externo con datos)
└──────┬───────┘
       │ XML-RPC
       ▼
┌──────────────────────────────────────┐
│  OdooConnection (services/)          │
│  - Lee credenciales del .env         │
│  - Establece conexión XML-RPC        │
│  - Autentica usuario                 │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Servicios Especializados            │
│  ├─ ReportService (reportes CxC)    │
│  ├─ CobranzaService (KPIs)          │
│  └─ SalesService (ventas)           │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  OdooManager (odoo_manager.py)       │
│  - Wrapper que agrupa servicios      │
│  - Mantiene compatibilidad           │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Flask App (app.py)                  │
│  - Rutas y lógica de negocio         │
│  - Procesa datos de Odoo             │
│  - Almacena en LOCAL_STORAGE         │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Templates HTML (Jinja2)             │
│  - Renderiza datos en tablas/gráficos│
│  - Dashboard, reportes, metas        │
└──────────────────────────────────────┘
```

---

## 📁 ESTRUCTURA DE ARCHIVOS CLAVE

### 1. **`app.py`** (Archivo Principal - 1559 líneas)
**Función**: Servidor Flask con todas las rutas y lógica de negocio

**Componentes principales**:
- **LOCAL_STORAGE** (líneas 26-30): Almacenamiento en memoria para metas
- **data_manager** (línea 22): Instancia de OdooManager para acceder a datos
- **Rutas implementadas**:
  - `/login` - Autenticación
  - `/sales` - Líneas de venta
  - `/dashboard` - Dashboard general de ventas
  - `/dashboard_linea` - Dashboard por línea comercial
  - `/meta` - Gestión de metas por línea
  - `/metas_vendedor` - Gestión de metas por vendedor
  - `/reporte_cxc_general` - Reporte CxC cuenta 12
  - `/reporte_internacional` - Reporte internacional
  - `/dashboard_cobranza_internacional` - Dashboard cobranza

**⚠️ PROBLEMA IDENTIFICADO**: 
- LOCAL_STORAGE es un diccionario en memoria que se pierde al reiniciar
- NO persiste datos entre sesiones

### 2. **`odoo_manager.py`** (Wrapper Principal)
**Función**: Punto de entrada único para acceder a todos los servicios

```python
class OdooManager:
    def __init__(self):
        self.connection = OdooConnection()      # Conexión base
        self.reports = ReportService()          # Reportes CxC
        self.cobranza = CobranzaService()       # KPIs cobranza
```

**Métodos importantes**:
- `authenticate_user()` - Login
- `get_sales_lines()` - Obtiene líneas de venta de Odoo
- `get_report_lines()` - Reportes CxC
- `get_all_sellers()` - Lista de vendedores

### 3. **`services/odoo_connection.py`** (Conexión a Odoo)
**Función**: Maneja la conexión XML-RPC con Odoo

```python
class OdooConnection:
    def __init__(self):
        self.url = os.getenv('ODOO_URL')           # ⚠️ CRÍTICO
        self.db = os.getenv('ODOO_DB')             # ⚠️ CRÍTICO
        self.username = os.getenv('ODOO_USER')     # ⚠️ CRÍTICO
        self.password = os.getenv('ODOO_PASSWORD') # ⚠️ CRÍTICO
```

**🔴 AQUÍ ESTÁ EL PROBLEMA**:
Si las variables de entorno NO están configuradas, la conexión falla y NO se extraen datos.

### 4. **`services/report_service.py`**
**Función**: Genera reportes de cuentas por cobrar

### 5. **`services/cobranza_service.py`**
**Función**: Calcula KPIs de cobranza (DSO, CEI, aging)

### 6. **`utils/calculators.py`**
**Función**: Funciones de cálculo (mora, días vencidos, aging)

### 7. **`utils/filters.py`**
**Función**: Filtros de datos (nacional/internacional)

---

## 🔧 CONFIGURACIÓN REQUERIDA

### Archivo `.env` (DEBE EXISTIR en raíz del proyecto)

```env
# Credenciales de Odoo
ODOO_URL=https://tu-servidor-odoo.com
ODOO_DB=nombre_base_datos
ODOO_USER=tu_usuario
ODOO_PASSWORD=tu_contraseña

# Flask
SECRET_KEY=una_clave_secreta_aleatoria
```

**⚠️ SIN ESTE ARCHIVO, LA APLICACIÓN NO FUNCIONA**

---

## 🚀 CÓMO FUNCIONA LA EXTRACCIÓN DE DATOS

### Ejemplo: Dashboard de Ventas

1. **Usuario accede a `/dashboard`** (línea 135 de app.py)

2. **Flask verifica sesión**:
   ```python
   if 'username' not in session:
       return redirect(url_for('login'))
   ```

3. **Obtiene parámetros**:
   ```python
   mes_seleccionado = request.args.get('mes', fecha_actual.strftime('%Y-%m'))
   ```

4. **Busca metas en LOCAL_STORAGE** (líneas 164-166):
   ```python
   metas_historicas = LOCAL_STORAGE.get('metas_por_linea', {})
   metas_del_mes = metas_historicas.get(mes_seleccionado, {}).get('metas', {})
   ```

5. **Llama a Odoo para obtener ventas** (líneas 192-196):
   ```python
   sales_data = data_manager.get_sales_lines(
       date_from=fecha_inicio,
       date_to=fecha_fin,
       limit=5000
   )
   ```

6. **Este método internamente**:
   - Va a `odoo_manager.py` → `get_sales_lines()`
   - Que usa `self.connection.execute_kw()` 
   - Que hace llamada XML-RPC a Odoo
   - **SI NO HAY CONEXIÓN**, retorna lista vacía `[]`

7. **Procesa los datos** (líneas 225-283):
   - Agrupa por línea comercial
   - Calcula ventas IPN
   - Agrupa por producto
   - Genera datos para gráficos

8. **Renderiza template** (líneas 372-382):
   ```python
   return render_template('dashboard_clean.html',
                        meses_disponibles=meses_disponibles,
                        kpis=kpis,
                        datos_lineas=datos_lineas,
                        ...)
   ```

---

## 🐛 PROBLEMAS IDENTIFICADOS

### ❌ **PROBLEMA 1: Archivo `.env` NO configurado o incorrecto**

**Síntomas**:
- La aplicación carga pero no muestra datos
- En consola: `[ERROR] Error en la conexion a Odoo: ...`
- Tablas y gráficos vacíos

**Solución**:
1. Verificar que existe `.env` en `dashboard-Cobranzas/`
2. Verificar credenciales correctas
3. Probar conexión manualmente

### ❌ **PROBLEMA 2: LOCAL_STORAGE se pierde al reiniciar**

**Código actual** (líneas 26-30 de app.py):
```python
LOCAL_STORAGE = {
    'metas_por_linea': {},
    'metas_vendedores': {},
    'equipos': {}
}
```

**Problema**: 
- Es un diccionario en memoria
- Al cerrar Flask, se pierden todas las metas guardadas
- Los usuarios tienen que re-ingresar metas cada vez

**Solución recomendada**:
- Migrar a SQLite o JSON persistente
- Ver sección "MEJORAS RECOMENDADAS" más abajo

### ❌ **PROBLEMA 3: Código deprecado - `google_sheets_manager.py`**

**Status**: ✅ YA ELIMINADO (según BITACORA.md)

Las líneas que lo referenciaban ya fueron reemplazadas por LOCAL_STORAGE.

### ⚠️ **PROBLEMA 4: Líneas 981, 994, 1011 - Referencias a gs_manager**

**Revisar en app.py**:
- Línea 981: Ya actualizada a `LOCAL_STORAGE['metas_vendedores']`
- Línea 994: Ya actualizada a `LOCAL_STORAGE.get('equipos', {})`
- Línea 1011: Ya actualizada a `LOCAL_STORAGE.get('metas_vendedores', {})`

✅ **CORRECTO** - No hay código deprecado aquí.

---

## 🔍 DIAGNÓSTICO PASO A PASO

### Paso 1: Verificar `.env`

Ejecuta en terminal:
```powershell
cd "C:\Users\jmontero\Desktop\GitHub Proyectos_AGV\dashboard-Cobranzas"
Get-Content .env
```

Debe mostrar las 5 variables (ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD, SECRET_KEY)

### Paso 2: Ejecutar la aplicación con logs

```powershell
python app.py
```

**Buscar en consola**:
- `[OK] Conexion a Odoo establecida exitosamente.` ✅ (Conexión OK)
- `[ERROR] Error en la conexion a Odoo: ...` ❌ (Credenciales incorrectas)
- `[WARN] No hay conexion a Odoo disponible` ❌ (No hay conexión)

### Paso 3: Probar login

1. Ir a `http://127.0.0.1:5002/login`
2. Ingresar credenciales del `.env`
3. Si funciona → Conexión OK
4. Si falla → Revisar credenciales

### Paso 4: Probar extracción de datos

En Python interactivo:
```python
from odoo_manager import OdooManager

manager = OdooManager()
print(f"Conectado: {manager.connection.is_connected()}")

# Probar obtener datos
ventas = manager.get_sales_lines(date_from='2024-01-01', date_to='2024-12-31', limit=10)
print(f"Ventas obtenidas: {len(ventas)}")
```

---

## 📊 FLUJO DE DATOS DETALLADO

### GET /dashboard

```
Usuario → Flask (/dashboard)
  ↓
app.py línea 136: def dashboard()
  ↓
Obtiene mes_seleccionado
  ↓
LOCAL_STORAGE.get('metas_por_linea', {}) → Busca metas guardadas
  ↓
data_manager.get_sales_lines(...) → Llama a Odoo
  ↓
odoo_manager.py → get_sales_lines()
  ↓
self.connection.search_read('account.move.line', ...)
  ↓
services/odoo_connection.py → execute_kw()
  ↓
xmlrpc.client → Llamada a ODOO
  ↓
ODOO responde con JSON de ventas
  ↓
Procesa datos (agrupa por línea, calcula KPIs)
  ↓
render_template('dashboard_clean.html', datos...)
  ↓
HTML renderizado al usuario
```

---

## 🛠️ MEJORAS RECOMENDADAS

### 1. **Persistencia de Datos (LOCAL_STORAGE)**

**Opción A: JSON File**
```python
import json

def save_storage():
    with open('storage.json', 'w') as f:
        json.dump(LOCAL_STORAGE, f)

def load_storage():
    try:
        with open('storage.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'metas_por_linea': {}, 'metas_vendedores': {}, 'equipos': {}}

LOCAL_STORAGE = load_storage()
```

**Opción B: SQLite** (Recomendado)
```python
# Migrar a base de datos SQLite con SQLAlchemy
```

### 2. **Caché de Consultas Odoo**

```python
from functools import lru_cache
from datetime import timedelta

@lru_cache(maxsize=100)
def get_cached_sales(date_from, date_to):
    return data_manager.get_sales_lines(date_from, date_to)
```

### 3. **Validación de Conexión al Inicio**

```python
# En app.py después de crear data_manager
if not data_manager.connection.is_connected():
    print("⚠️ ADVERTENCIA: No se pudo conectar a Odoo")
    print("   Verifica tu archivo .env")
```

---

## 📝 CHECKLIST DE SOLUCIÓN

### Para que la aplicación funcione correctamente:

- [ ] Verificar que existe `.env` en `dashboard-Cobranzas/`
- [ ] Validar credenciales de Odoo en `.env`
- [ ] Ejecutar `python app.py` y verificar `[OK] Conexion a Odoo establecida`
- [ ] Probar login con credenciales del `.env`
- [ ] Acceder a dashboard y verificar que aparecen datos
- [ ] Si no aparecen datos, revisar consola para errores
- [ ] Considerar implementar persistencia para LOCAL_STORAGE

---

## 🚨 CÓDIGO DEPRECADO IDENTIFICADO

### ✅ **YA ELIMINADO**:
- `google_sheets_manager.py` - Eliminado según BITACORA.md
- Referencias a `gs_manager` en app.py - Ya actualizadas

### ⚠️ **POTENCIALMENTE INNECESARIO**:

**Archivo**: `conectar_odoo.py`
- **Descripción**: Podría ser un script de prueba antiguo
- **Acción**: Revisar si se usa, si no, eliminar

**Archivos en `/test`**:
- `test_dashboard_cobranza_internacional.html`
- `test_odoo_manager.py`
- `test_reporte_cxc_general.html`
- **Acción**: Mantener solo si son tests útiles

**Archivo**: `INSTRUCCIONES_GOOGLE_SHEETS.md`
- **Descripción**: Instrucciones para Google Sheets (ya no usado)
- **Acción**: Eliminar

---

## 🎯 CONCLUSIÓN

### El problema principal es:

**LA APLICACIÓN NO EXTRAE DATOS PORQUE**:
1. ❌ El archivo `.env` no está configurado correctamente
2. ❌ Las credenciales de Odoo son incorrectas
3. ❌ No hay conexión al servidor de Odoo

### Solución inmediata:

1. **Verificar archivo `.env`** con credenciales correctas
2. **Ejecutar `python app.py`** y buscar mensaje de conexión
3. **Probar login** para confirmar autenticación
4. **Si persiste el problema**, revisar logs de consola

### Próximos pasos:

1. Implementar persistencia para LOCAL_STORAGE (SQLite)
2. Agregar validación de conexión al inicio
3. Implementar caché para consultas frecuentes
4. Eliminar código deprecado (archivos de Google Sheets)

---

**Fecha**: 10 de Octubre, 2025  
**Proyecto**: Dashboard Cobranzas - AGV Agrovet Market  
**Versión**: 4.1.0


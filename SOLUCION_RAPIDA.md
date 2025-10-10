# 🚀 SOLUCIÓN RÁPIDA - No Extrae Datos

## ⚡ PROBLEMA PRINCIPAL

**La aplicación NO extrae datos de Odoo** porque:
- ❌ Falta configurar el archivo `.env`
- ❌ Las credenciales están incorrectas
- ❌ No hay conexión al servidor Odoo

---

## 🔧 SOLUCIÓN EN 3 PASOS

### PASO 1: Verificar archivo `.env`

**Ubicación**: `dashboard-Cobranzas/.env`

Debe contener estas 5 variables:

```env
ODOO_URL=https://tu-servidor-odoo.com
ODOO_DB=nombre_de_base_datos
ODOO_USER=tu_usuario_odoo
ODOO_PASSWORD=tu_contraseña_odoo
SECRET_KEY=clave_secreta_aleatoria_123456789
```

**⚠️ SI NO EXISTE**: Créalo manualmente con las credenciales correctas

### PASO 2: Ejecutar diagnóstico

Abre PowerShell en la carpeta del proyecto:

```powershell
cd "C:\Users\jmontero\Desktop\GitHub Proyectos_AGV\dashboard-Cobranzas"
python diagnostico.py
```

Este script verificará:
- ✅ Archivos del proyecto
- ✅ Variables de entorno
- ✅ Conexión a Odoo
- ✅ Extracción de datos

### PASO 3: Ejecutar la aplicación

```powershell
python app.py
```

**Buscar en la consola**:
- `[OK] Conexion a Odoo establecida exitosamente.` → ✅ **BUENO**
- `[ERROR] Error en la conexion a Odoo: ...` → ❌ **MAL** (revisar .env)

---

## 🔍 SI PERSISTE EL PROBLEMA

### Verificación Manual del `.env`

```powershell
Get-Content .env
```

Debe mostrar las 5 líneas con valores (no vacíos)

### Probar conexión manualmente

Crear archivo `test_conexion.py`:

```python
from dotenv import load_dotenv
import os

load_dotenv()

print("ODOO_URL:", os.getenv('ODOO_URL'))
print("ODOO_DB:", os.getenv('ODOO_DB'))
print("ODOO_USER:", os.getenv('ODOO_USER'))
print("ODOO_PASSWORD:", "***" if os.getenv('ODOO_PASSWORD') else "NO CONFIGURADA")
print("SECRET_KEY:", "***" if os.getenv('SECRET_KEY') else "NO CONFIGURADA")
```

Ejecutar:
```powershell
python test_conexion.py
```

---

## 📊 FLUJO DE DATOS SIMPLIFICADO

```
1. Usuario → http://127.0.0.1:5002/login
         ↓
2. Flask lee .env y conecta a Odoo
         ↓
3. Si conexión OK → Extrae datos
         ↓
4. Procesa y almacena en LOCAL_STORAGE
         ↓
5. Muestra en templates HTML
```

**Si falla en paso 2 → No hay datos**

---

## 🛠️ CÓDIGO DEPRECADO A ELIMINAR

### Archivo 1: `INSTRUCCIONES_GOOGLE_SHEETS.md`
**Razón**: Ya no usamos Google Sheets  
**Acción**: Eliminar

### Archivo 2: `conectar_odoo.py`
**Razón**: Posiblemente script antiguo de prueba  
**Acción**: Revisar si se usa, si no → Eliminar

### Archivos en carpeta `/test`
**Razón**: Tests antiguos  
**Acción**: Mantener solo si son útiles

---

## ✅ CHECKLIST DE SOLUCIÓN

- [ ] Existe archivo `.env` en `dashboard-Cobranzas/`
- [ ] `.env` tiene las 5 variables con valores correctos
- [ ] Ejecutar `python diagnostico.py` → Todo en verde
- [ ] Ejecutar `python app.py` → Ver mensaje `[OK] Conexion a Odoo establecida`
- [ ] Ir a login y autenticar
- [ ] Dashboard muestra datos

---

## 📞 AYUDA ADICIONAL

1. **Leer documentación completa**: `EXPLICACION_PROYECTO.md`
2. **Ejecutar diagnóstico**: `python diagnostico.py`
3. **Revisar logs de consola** cuando ejecutas `python app.py`

---

**Fecha**: 10 de Octubre, 2025  
**Proyecto**: Dashboard Cobranzas

